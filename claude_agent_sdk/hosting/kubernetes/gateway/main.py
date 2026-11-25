"""
Gateway service for the Kubernetes tier of the Agent SDK hosting cookbook.

This is the single entry point that clients talk to.  It:
  1. Maps ``session_id`` → agent pod (Redis), creating pods on demand via k8s.py.
  2. Relays ``POST /sessions/{id}/messages`` to the right pod and streams the
     SSE response back unchanged (proxy.py).
  3. Reaps pods that have been idle past ``IDLE_TIMEOUT_S``.

Architecture:
  Client <--HTTP/SSE--> Gateway (this file) <--HTTP/SSE--> Agent Pod (one per session)

Redis stores only routing metadata (pod IP, timestamps).  The gateway is
stateless — you can run multiple replicas behind a load balancer.
"""

import asyncio
import logging
import os
import re
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from k8s import (
    create_agent_pod,
    delete_agent_pod,
    get_pool_status,
    initialize_standby_pool,
)
from proxy import relay_sse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Agent pods with no traffic for this many seconds are deleted.  900s (15 min)
# is a reasonable default for interactive sessions; raise it for long-running
# autonomous tasks.  Activity is stamped when a request *arrives*, not while a
# stream is in flight — keep this comfortably above your longest expected turn.
IDLE_TIMEOUT_S = int(os.getenv("IDLE_TIMEOUT_S", "900"))

# How long a request will wait for another in-flight request to finish
# provisioning the same session's pod (see _ensure_session_pod).
PROVISION_TIMEOUT_S = 180

# Reject oversized request bodies before they reach the JSON parser or the
# agent pod. 256 KB is generous for a prompt.
MAX_BODY_BYTES = 256 * 1024

# Static bearer-token → tenant map, e.g. ``GATEWAY_TENANTS="tokenA:alice,tokenB:bob"``.
# Every request (except /health) must present ``Authorization: Bearer <token>``
# for one of these entries; the matching tenant becomes the caller's identity
# and sessions are scoped to it.  Unset = no auth and a single shared tenant —
# acceptable only for local poking, never for anything reachable by others.
# A pair with an empty token (":alice") is dropped rather than mapped — an
# empty key would make the empty Authorization header a valid credential.
_TOKEN_TO_TENANT: dict[str, str] = {}
for _pair in os.getenv("GATEWAY_TENANTS", "").split(","):
    _parts = _pair.split(":", 1)
    if len(_parts) != 2:
        continue
    _token, _tenant = _parts[0].strip(), _parts[1].strip()
    if not _token:
        continue
    _TOKEN_TO_TENANT[_token] = _tenant
logger.info("gateway: loaded %d tenant token(s)", len(_TOKEN_TO_TENANT))

# Session IDs must match this pattern to prevent path traversal / label abuse.
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _validate_session_id(session_id: str) -> str:
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id: 1-64 alphanumeric / hyphen / underscore",
        )
    return session_id


# Module-level Redis client — ``from_url()`` doesn't open a socket; the
# connection pool dials lazily on first await.
redis_client: redis.Redis = redis.from_url(REDIS_URL, decode_responses=True)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: warm the standby pool and start the idle reaper.
    Shutdown: stop the reaper and close Redis.
    """
    await initialize_standby_pool()
    reaper = asyncio.create_task(_reap_idle_loop())
    yield
    reaper.cancel()
    await redis_client.aclose()


app = FastAPI(title="Claude Agent Gateway (k8s)", lifespan=lifespan)


# Only enforces the cap for requests with Content-Length; chunked bodies
# pass through. In production put a real body-size limit on the gateway/LB.
@app.middleware("http")
async def _limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "request body too large"})
    return await call_next(request)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def authenticate(request: Request) -> str:
    """Return the caller's tenant id.  Swap this for your IdP.

    The demo enforces tenant isolation: each bearer token in ``GATEWAY_TENANTS``
    maps to a tenant, every session is owned by the tenant that created it, and
    a caller presenting another tenant's token gets a 403.  What's *not* real is
    the credential itself — a static token map with no issuance, rotation, or
    revocation.  A production deployment validates an OIDC/JWT/mTLS credential
    here and derives the tenant from its claims; the ownership checks downstream
    stay exactly the same.
    """
    if not _TOKEN_TO_TENANT:
        return "anonymous"  # GATEWAY_TENANTS unset — open access, single tenant
    auth = request.headers.get("authorization", "")
    presented = auth.removeprefix("Bearer ") if auth.startswith("Bearer ") else ""
    if not presented:
        raise HTTPException(status_code=401, detail="unauthorized")
    # compare_digest over every entry so the lookup isn't a timing oracle.
    matched: str | None = None
    for token, tenant in _TOKEN_TO_TENANT.items():
        if secrets.compare_digest(presented, token):
            matched = tenant
    if matched is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return matched


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Liveness/readiness probe.  Unauthenticated so kubelet can call it."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


# ---------------------------------------------------------------------------
# Session → pod mapping
# ---------------------------------------------------------------------------


async def _owned_pod_ip(session_id: str, tenant: str) -> str | None:
    """Return the session's pod IP if it exists and belongs to ``tenant``.

    ``None`` means the session doesn't exist yet — the caller may create it
    and becomes its owner.  403 if it exists but was created by a different
    tenant: this is the ownership check the gateway exists to enforce, and
    it runs on *every* lookup, not just at creation time.
    """
    data = await redis_client.hgetall(f"session:{session_id}")
    if not data:
        return None
    if data.get("tenant") != tenant:
        raise HTTPException(status_code=403, detail="session belongs to another tenant")
    return data.get("pod_ip")


async def _ensure_session_pod(session_id: str, tenant: str) -> str:
    """Look up or provision the pod for a session.  Returns its IP.

    Redis hash ``session:{id}`` is the source of truth for routing *and*
    ownership: the tenant that first POSTs to a ``session_id`` is recorded as
    its owner, and every subsequent lookup re-checks that the caller matches.

    A per-session ``SET NX`` lock guards provisioning: without it, a client
    retry that lands while the first request is still waiting for the pod
    would claim a *second* pod for the same session and leak it until the
    idle reaper runs.  The loser of the race waits for the winner's mapping
    to appear instead — and then still goes through the ownership check, so
    two tenants racing to create the same ``session_id`` can't end up sharing
    a pod.
    """
    pod_ip = await _owned_pod_ip(session_id, tenant)
    if pod_ip:
        return pod_ip

    lock_key = f"session:{session_id}:provisioning"
    got_lock = await redis_client.set(lock_key, "1", nx=True, ex=PROVISION_TIMEOUT_S)
    if not got_lock:
        for _ in range(PROVISION_TIMEOUT_S):
            await asyncio.sleep(1)
            pod_ip = await _owned_pod_ip(session_id, tenant)
            if pod_ip:
                return pod_ip
        raise HTTPException(status_code=503, detail="session pod is still starting; retry shortly")

    try:
        pod_ip = await create_agent_pod(session_id)
        now = datetime.now(UTC).isoformat()
        await redis_client.hset(
            f"session:{session_id}",
            mapping={
                "id": session_id,
                "tenant": tenant,
                "status": "active",
                "pod_ip": pod_ip,
                "created_at": now,
                "last_activity": now,
            },
        )
        await redis_client.sadd("sessions:active", session_id)
        return pod_ip
    finally:
        await redis_client.delete(lock_key)


# ---------------------------------------------------------------------------
# The one route that matters
# ---------------------------------------------------------------------------


@app.post("/sessions/{session_id}/messages")
async def post_message(
    session_id: str,
    request: Request,
    tenant: str = Depends(authenticate),
):
    """Forward a turn to the session's agent pod and stream SSE back.

    Same path and shape as ``hosting/server.py`` (Tier 1/2), so client code
    written against the Docker or Modal tier works unchanged here — only the
    base URL moves.  The first POST on a ``session_id`` makes the caller's
    tenant its owner; other tenants get a 403 from then on.
    """
    _validate_session_id(session_id)
    body = await request.json()
    pod_ip = await _ensure_session_pod(session_id, tenant)
    await redis_client.hset(f"session:{session_id}", "last_activity", datetime.now(UTC).isoformat())
    try:
        stream = await relay_sse(pod_ip, session_id, body)
    except HTTPException as exc:
        if exc.status_code != 502:
            raise
        # The mapped pod is gone (evicted, OOM-killed, node restarted) but the
        # Redis entry outlived it.  Delete the dead pod object (no-op if it's
        # already gone), drop only the stale ``pod_ip`` field — keeping the
        # rest of the hash means the session never becomes ownerless, so no
        # other tenant can claim the id mid-recovery — and provision a fresh
        # pod once before giving up.  Without this, every request on the
        # session keeps 502ing until the idle reaper happens to clean it up.
        logger.warning(f"Stale pod mapping for session {session_id}; reprovisioning")
        await delete_agent_pod(session_id)
        await redis_client.hdel(f"session:{session_id}", "pod_ip")
        pod_ip = await _ensure_session_pod(session_id, tenant)
        stream = await relay_sse(pod_ip, session_id, body)
    return StreamingResponse(stream, media_type="text/event-stream")


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    tenant: str = Depends(authenticate),
):
    """Delete the session's pod and forget the mapping.

    Owner-only: deleting someone else's session is just as much a breach as
    reading it.  Deleting a session that doesn't exist is a 200 no-op so
    clients can retry without special-casing — and it must not touch the
    cluster, or it could kill a pod another tenant is still provisioning
    (the pod exists before its Redis record does).
    """
    _validate_session_id(session_id)
    if not await redis_client.exists(f"session:{session_id}"):
        return {"status": "deleted"}  # absent — nothing to do, touch nothing
    await _owned_pod_ip(session_id, tenant)  # 403 unless the caller owns it
    await delete_agent_pod(session_id)
    await redis_client.delete(f"session:{session_id}")
    await redis_client.srem("sessions:active", session_id)
    return {"status": "deleted"}


@app.get("/api/pool")
async def pool_status(_tenant: str = Depends(authenticate)):
    """Standby pool size — useful for monitoring."""
    return await get_pool_status()


# ---------------------------------------------------------------------------
# Idle reaper
# ---------------------------------------------------------------------------


async def _reap_idle_loop():
    """Background task: delete pods whose session has been idle too long.

    Without this, every session would hold a pod (and its CPU/memory request)
    forever.  Runs every 60s; on each pass it checks ``last_activity`` for all
    active sessions and reaps any past the timeout.

    Pod deletes and Redis cleanup are idempotent (404s are swallowed), so it's
    safe for several gateway replicas to run this loop concurrently — they
    just race to the same outcome.
    """
    while True:
        try:
            now = datetime.now(UTC)
            for session_id in await redis_client.smembers("sessions:active"):
                last = await redis_client.hget(f"session:{session_id}", "last_activity")
                if not last:
                    continue
                idle = (now - datetime.fromisoformat(last)).total_seconds()
                if idle > IDLE_TIMEOUT_S:
                    logger.info(f"Reaping idle session {session_id} ({idle:.0f}s idle)")
                    await delete_agent_pod(session_id)
                    await redis_client.delete(f"session:{session_id}")
                    await redis_client.srem("sessions:active", session_id)
        except Exception:
            logger.exception("idle reaper pass failed")
        await asyncio.sleep(60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)  # noqa: S104 — container-internal server
