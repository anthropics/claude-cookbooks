"""Sprites self-hosted sandbox demo — webhook variant.

FastAPI app: receives the session.status_run_started webhook, drains the
environment work queue, and per item creates a Sprite
([sprites.dev](https://sprites.dev), Fly.io's stateful sandboxes) running the
provider-agnostic ``sandbox_runner.py`` (see ``sprite_sandbox.spawn``). Deploy
this anywhere that can serve HTTP and reach the Sprites API (Fly, Render, a VM,
etc.).

The webhook is a wake-up signal only — each delivery drains *all* pending work
items, so a single arriving webhook recovers any earlier missed deliveries. For
a no-public-endpoint alternative that polls continuously, see
``sprites_poller.py``.

No org API key reaches the runner: the webhook polls with the environment key,
and each Sprite authenticates with that same environment key — the single
credential for both the control plane and the per-session calls.

Env on the orchestrator host:
  ANTHROPIC_WEBHOOK_SECRET, ANTHROPIC_BASE_URL,
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  SPRITES_API_KEY, SPRITES_API_URL (optional)
"""

import os
from collections.abc import Mapping
from functools import cache

import anthropic
from anthropic.types.beta import UnwrapWebhookEvent
from fastapi import FastAPI, HTTPException, Request

from sprite_sandbox import find_live, spawn

app = FastAPI()


@cache
def _client() -> anthropic.AsyncAnthropic:
    """Shared client for both webhook verification and the work poller.

    Async because ``client.beta.environments.work.poller(...)`` is async-only.
    ``unwrap()`` is synchronous even on the async client — do not ``await`` it.
    """
    return anthropic.AsyncAnthropic(
        auth_token=os.environ["ANTHROPIC_ENVIRONMENT_KEY"],
        webhook_key=os.environ["ANTHROPIC_WEBHOOK_SECRET"],
    )


def _verify_webhook(
    client: anthropic.AsyncAnthropic, raw: bytes, headers: "Mapping[str, str]"
) -> UnwrapWebhookEvent:
    from standardwebhooks import WebhookVerificationError

    try:
        return client.beta.webhooks.unwrap(raw.decode(), headers=headers)
    except (WebhookVerificationError, KeyError) as e:
        print(f"[webhook] signature reject: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(
            status_code=401, detail="signature verification failed"
        ) from None


async def _drain_work(
    client: anthropic.AsyncAnthropic, environment_id: str
) -> list[dict]:
    """Drain the queue via the SDK poller, spawning a Sprite per work item.

    ``drain=True`` returns when the queue is empty (the webhook handler must
    respond, not loop forever). ``auto_stop=False`` because each item is handed
    off to a detached Sprite that owns ``/stop`` — the poller must not terminate
    the lease out from under it.
    """
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    spawned: list[dict] = []
    async for work in client.beta.environments.work.poller(
        environment_id=environment_id,
        environment_key=environment_key,
        block_ms=None,  # None -> omit -> non-blocking. The API rejects block_ms=0.
        reclaim_older_than_ms=2000,
        drain=True,
        auto_stop=False,
    ):
        if work.data.type != "session":
            print(f"[webhook] skipping work={work.id} type={work.data.type}", flush=True)
            continue
        session_id = work.data.id
        try:
            name = find_live(session_id) or spawn(
                session_id,
                environment_id=environment_id,
                work_id=work.id,
                environment_key=environment_key,
            )
            print(
                f"[webhook] work={work.id} session={session_id} sprite={name}",
                flush=True,
            )
            spawned.append(
                {"session_id": session_id, "work_id": work.id, "sprite": name}
            )
        except Exception as e:
            detail = type(e).__name__
            print(
                f"[webhook] FAILED work={work.id} session={session_id}: {detail}",
                flush=True,
            )
            spawned.append(
                {"session_id": session_id, "work_id": work.id, "error": detail}
            )
    return spawned


@app.post("/")
async def webhook(request: Request) -> dict:
    raw = await request.body()
    client = _client()
    event = _verify_webhook(client, raw, request.headers)

    if event.data.type != "session.status_run_started":
        return {"status": "ignored", "event_type": event.data.type}

    spawned = await _drain_work(client, os.environ["ANTHROPIC_ENVIRONMENT_ID"])
    return {"status": "ok", "event_type": event.data.type, "spawned": spawned}
