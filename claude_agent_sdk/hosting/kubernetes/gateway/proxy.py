"""Transparent SSE relay between client and agent pod.

The gateway doesn't understand the agent's event stream — it just pipes
bytes through.  ``hosting/server.py`` inside the pod speaks Server-Sent
Events on ``POST /sessions/{id}/messages``; we open that request and
forward the raw SSE bytes to the caller without parsing them.  If the
agent's wire format changes, this file doesn't care.
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

AGENT_PORT = 8000

# Connect/write/pool bounded so a dead pod IP fails fast; read unbounded
# because an agent turn can legitimately stream for minutes.
_TIMEOUT = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)


async def relay_sse(
    pod_ip: str,
    session_id: str,
    body: dict,
) -> AsyncIterator[bytes]:
    """POST the request body to the agent pod and return a raw-SSE byte stream.

    The upstream connection is established **before** this coroutine returns,
    so a dead/unreachable pod surfaces as a clean 502 to the caller instead
    of a dropped connection mid-stream (which clients see as ``curl (18)``).
    The caller awaits this coroutine and wraps the returned iterator in a
    ``StreamingResponse`` with ``media_type="text/event-stream"``.

    ``aiter_raw()`` (not ``aiter_lines()``) preserves multi-line ``data:``
    payloads and the blank-line event delimiter exactly — no re-framing.
    """
    url = f"http://{pod_ip}:{AGENT_PORT}/sessions/{session_id}/messages"
    client = httpx.AsyncClient(timeout=_TIMEOUT)
    try:
        req = client.build_request("POST", url, json=body)
        upstream = await client.send(req, stream=True)
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        await client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"agent pod {pod_ip} unreachable: {exc}",
        ) from exc

    if upstream.status_code >= 400:
        body_bytes = await upstream.aread()
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"agent pod returned {upstream.status_code}: "
            f"{body_bytes.decode(errors='replace')[:200]}",
        )

    async def _stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        except httpx.HTTPError as exc:
            # The pod died mid-stream (OOM-kill, eviction).  The HTTP status
            # already went out, so we can't 502 — emit the contract's
            # ``event: error`` frame instead of dropping the connection.
            logger.warning(f"Upstream stream from {pod_ip} aborted: {exc!r}")
            payload = json.dumps({"message": f"agent pod stream aborted: {exc}"})
            yield f"event: error\ndata: {payload}\n\n".encode()
        finally:
            await upstream.aclose()
            await client.aclose()

    return _stream()
