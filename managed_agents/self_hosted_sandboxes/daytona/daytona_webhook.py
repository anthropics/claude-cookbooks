"""Daytona analogue of modal_sandbox_webhook.py.

FastAPI app: receives the session.status_run_started webhook, drains the
environment work queue, and per item creates a Daytona sandbox running the
provider-agnostic ``sandbox_runner.py``. Deploy this anywhere that can serve
HTTP and reach the Daytona API (Fly, Render, a VM, etc.).

The webhook is a wake-up signal only — each delivery drains *all* pending work
items, so a single arriving webhook recovers any earlier missed deliveries.

Env on the orchestrator host:
  ANTHROPIC_WEBHOOK_SECRET, ANTHROPIC_BASE_URL,
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  DAYTONA_API_KEY, DAYTONA_API_URL
"""

import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import anthropic
from anthropic.types.beta import UnwrapWebhookEvent
from daytona_sdk import CreateSandboxParams, Daytona
from fastapi import FastAPI, HTTPException, Request

SDK_PACKAGE = "anthropic"
# Same provider-agnostic sandbox_runner.py the Modal demo uses.
RUNNER_SRC = (Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py").read_text()

app = FastAPI()
daytona = Daytona()  # reads DAYTONA_API_KEY / DAYTONA_API_URL from env


@cache
def _client() -> anthropic.AsyncAnthropic:
    """Shared client for both webhook verification and the work poller.

    Async because ``client.beta.environments.work.poller(...)`` is async-only
    (it lives on ``AsyncWork``). ``unwrap()`` is synchronous even on the async
    client — do not ``await`` it. The ``whsec_`` secret is passed to
    ``webhook_key`` as-is: the SDK decodes its URL-safe base64 internally.
    """
    return anthropic.AsyncAnthropic(
        auth_token=os.environ["ANTHROPIC_ENVIRONMENT_KEY"],
        webhook_key=os.environ["ANTHROPIC_WEBHOOK_SECRET"],
    )


def _verify_webhook(
    client: anthropic.AsyncAnthropic, raw: bytes, headers: "Mapping[str, str]"
) -> UnwrapWebhookEvent:
    # `unwrap()` verifies via `standardwebhooks` and lets its
    # `WebhookVerificationError` propagate unwrapped — import it the same lazy
    # way the SDK does (it's the `anthropic[webhooks]` extra).
    from standardwebhooks import WebhookVerificationError

    try:
        return client.beta.webhooks.unwrap(raw.decode(), headers=headers)
    except (WebhookVerificationError, KeyError) as e:
        # Messages are signature/config shaped, never the request body — safe
        # to log. Other exceptions propagate (they indicate a bug, not a bad
        # delivery).
        print(f"[webhook] signature reject: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=401, detail="signature verification failed") from None


def _spawn(session_id: str, *, environment_id: str, work_id: str, environment_key: str) -> str:
    """Create a Daytona sandbox and start sandbox_runner.py inside it."""
    sb = daytona.create(
        CreateSandboxParams(
            language="python",
            labels={"session_id": session_id},
            # Same env contract as `ant beta:worker poll --on-work`: sandbox_runner.py
            # reads these to build the client and run the worker's handle_item().
            # ANTHROPIC_ENVIRONMENT_KEY is the runner's single credential.
            env_vars={
                "ANTHROPIC_BASE_URL": os.environ.get(
                    "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
                ),
                "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
                "ANTHROPIC_SESSION_ID": session_id,
                "ANTHROPIC_ENVIRONMENT_ID": environment_id,
                "ANTHROPIC_WORK_ID": work_id,
            },
        )
    )
    sb.fs.upload_file("/root/sandbox_runner.py", RUNNER_SRC.encode())
    sb.process.exec(f"pip install -q {SDK_PACKAGE}", timeout=180)
    sb.process.exec("nohup python /root/sandbox_runner.py >/tmp/runner.log 2>&1 &")
    return sb.id


def _find_live(session_id: str) -> str | None:
    for sb in daytona.list(labels={"session_id": session_id}):
        if sb.state == "started":
            return sb.id
    return None


async def _drain_work(client: anthropic.AsyncAnthropic, environment_id: str) -> list[dict]:
    """Drain the queue via the SDK poller, spawning a sandbox per work item.

    ``client.beta.environments.work.poller`` is the user-facing entry point: it
    builds a scoped sub-client from the environment key and yields each ack'd
    work item. It is async-only (lives on ``AsyncWork``). ``drain=True`` returns
    when the queue is empty (the webhook handler must respond, not loop forever).
    ``auto_stop=False`` because each item is handed off to a detached Daytona
    sandbox that owns ``/stop`` — the poller must not terminate the lease out
    from under it.
    """
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    spawned: list[dict] = []
    async for work in client.beta.environments.work.poller(
        environment_id=environment_id,
        environment_key=environment_key,
        # None -> omit -> non-blocking. The API rejects block_ms=0.
        block_ms=None,
        reclaim_older_than_ms=2000,
        drain=True,
        auto_stop=False,
    ):
        if work.data.type != "session":
            print(f"[webhook] skipping work={work.id} type={work.data.type}", flush=True)
            continue
        session_id = work.data.id
        try:
            existing = _find_live(session_id)
            if existing is not None:
                print(
                    f"[webhook] work={work.id} session={session_id} sandbox={existing} (live)",
                    flush=True,
                )
                spawned.append(
                    {
                        "session_id": session_id,
                        "work_id": work.id,
                        "sandbox_id": existing,
                        "created": False,
                    }
                )
                continue
            sandbox_id = _spawn(
                session_id,
                environment_id=environment_id,
                work_id=work.id,
                environment_key=environment_key,
            )
            print(
                f"[webhook] work={work.id} session={session_id} sandbox={sandbox_id} (created)",
                flush=True,
            )
            spawned.append(
                {
                    "session_id": session_id,
                    "work_id": work.id,
                    "sandbox_id": sandbox_id,
                    "created": True,
                }
            )
        except Exception as e:
            # SDK / Daytona exceptions can embed request context, so log type only.
            detail = type(e).__name__
            print(
                f"[webhook] FAILED work={work.id} session={session_id}: {detail}",
                flush=True,
            )
            spawned.append({"session_id": session_id, "work_id": work.id, "error": detail})
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
