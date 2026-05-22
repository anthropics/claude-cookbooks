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
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

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

# Optional shared-secret bearer token.  If set, every request (except /health)
# must present ``Authorization: Bearer <token>``.  Replace with your IdP in
# production — see "What this doesn't give you" in the README.
GATEWAY_AUTH_TOKEN = os.getenv("GATEWAY_AUTH_TOKEN") or None

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


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate(request: Request) -> str:
    """Return the caller's tenant id.  Swap this for your IdP.

    The cookbook ships a static bearer token (or no auth at all if
    ``GATEWAY_AUTH_TOKEN`` is unset) and a single hard-coded tenant.  A real
    deployment validates an OIDC/JWT/mTLS credential here and returns the
    caller's tenant so different tenants can't guess each other's session IDs.
    """
    if GATEWAY_AUTH_TOKEN:
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {GATEWAY_AUTH_TOKEN}":
            raise HTTPException(status_code=401, detail="unauthorized")
    return "cookbook"


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

async def _ensure_session_pod(session_id: str) -> str:
    """Look up or provision the pod for a session.  Returns its IP.

    Redis hash ``session:{id}`` is the source of truth for routing.  If we
    don't know a pod yet, claim or create one via k8s.py and record it.

    A per-session ``SET NX`` lock guards provisioning: without it, a client
    retry that lands while the first request is still waiting for the pod
    would claim a *second* pod for the same session and leak it until the
    idle reaper runs.  The loser of the race waits for the winner's mapping
    to appear instead.
    """
    pod_ip = await redis_client.hget(f"session:{session_id}", "pod_ip")
    if pod_ip:
        return pod_ip

    lock_key = f"session:{session_id}:provisioning"
    got_lock = await redis_client.set(lock_key, "1", nx=True, ex=PROVISION_TIMEOUT_S)
    if not got_lock:
        for _ in range(PROVISION_TIMEOUT_S):
            await asyncio.sleep(1)
            pod_ip = await redis_client.hget(f"session:{session_id}", "pod_ip")
            if pod_ip:
                return pod_ip
        raise HTTPException(
            status_code=503, detail="session pod is still starting; retry shortly"
        )

    try:
        pod_ip = await create_agent_pod(session_id)
        now = datetime.now(UTC).isoformat()
        await redis_client.hset(
            f"session:{session_id}",
            mapping={
                "id": session_id,
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
    _tenant: str = Depends(authenticate),
):
    """Forward a turn to the session's agent pod and stream SSE back.

    Same path and shape as ``hosting/server.py`` (Tier 1/2), so client code
    written against the Docker or Modal tier works unchanged here — only the
    base URL moves.
    """
    _validate_session_id(session_id)
    body = await request.json()
    pod_ip = await _ensure_session_pod(session_id)
    await redis_client.hset(
        f"session:{session_id}", "last_activity", datetime.now(UTC).isoformat()
    )
    try:
        stream = await relay_sse(pod_ip, session_id, body)
    except HTTPException as exc:
        if exc.status_code != 502:
            raise
        # The mapped pod is gone (evicted, OOM-killed, node restarted) but the
        # Redis entry outlived it.  Delete the dead pod object (no-op if it's
        # already gone), drop the stale mapping, and provision a fresh pod once
        # before giving up — without this, every request on the session keeps
        # 502ing until the idle reaper happens to clean it up.
        logger.warning(f"Stale pod mapping for session {session_id}; reprovisioning")
        await delete_agent_pod(session_id)
        await redis_client.delete(f"session:{session_id}")
        await redis_client.srem("sessions:active", session_id)
        pod_ip = await _ensure_session_pod(session_id)
        stream = await relay_sse(pod_ip, session_id, body)
    return StreamingResponse(stream, media_type="text/event-stream")


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    _tenant: str = Depends(authenticate),
):
    """Delete the session's pod and forget the mapping."""
    _validate_session_id(session_id)
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
                last = await redis_client.hget(
                    f"session:{session_id}", "last_activity"
                )
                if not last:
                    continue
                idle = (now - datetime.fromisoformat(last)).total_seconds()
                if idle > IDLE_TIMEOUT_S:
                    logger.info(
                        f"Reaping idle session {session_id} ({idle:.0f}s idle)"
                    )
                    await delete_agent_pod(session_id)
                    await redis_client.delete(f"session:{session_id}")
                    await redis_client.srem("sessions:active", session_id)
        except Exception:
            logger.exception("idle reaper pass failed")
        await asyncio.sleep(60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
