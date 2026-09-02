"""Modal app: Anthropic session webhook → drain environment work queue → spin up a Sandbox per item.

The webhook is a wake-up signal only. Each delivery drains *all* pending work
items (not just the one that triggered it), so a single arriving webhook
recovers any earlier missed deliveries.

Flow per webhook delivery:
  1. Verify the Standard Webhooks signature via ``client.beta.webhooks.unwrap()``.
  2. Only act on data.type == "session.status_run_started".
  3. ``client.beta.environments.work.poller(drain=True, auto_stop=False)``
     polls until empty; each yielded ``work`` item has already been ack'd.
     Get-or-create a Modal Sandbox keyed on the work item's session_id running
     sandbox_runner.py, passing the environment key — the single credential the
     runner uses for everything. ``auto_stop=False`` because the sandbox owns
     ``/stop``, not the webhook — see sandbox_runner.py.

Secrets (modal secret create cma-self-hosted-sandboxes-secrets ...):
  ANTHROPIC_WEBHOOK_SECRET   - issued by Anthropic at webhook registration
  ANTHROPIC_ENVIRONMENT_ID   - the self-hosted environment id
  ANTHROPIC_ENVIRONMENT_KEY  - the environment key: Bearer auth for the work
                               poll/ack/stop, and the runner's only credential
  ANTHROPIC_BASE_URL         - optional, default https://api.anthropic.com

Deploy:
  modal secret create cma-self-hosted-sandboxes-secrets \
      ANTHROPIC_WEBHOOK_SECRET=placeholder \
      ANTHROPIC_ENVIRONMENT_KEY=placeholder \
      ANTHROPIC_ENVIRONMENT_ID=env_01...
  modal deploy modal_sandbox_webhook.py
  # register the printed URL with Anthropic, then re-create the secret with --force.
"""

import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import anthropic
import modal
from anthropic.types.beta import UnwrapWebhookEvent
from fastapi import HTTPException, Request

APP_NAME = "cma-self-hosted-sandboxes"
SECRET_NAME = "cma-self-hosted-sandboxes-secrets"

SDK_PACKAGE = "anthropic"
RUNNER_PATH = "/root/sandbox_runner.py"

app = modal.App(APP_NAME)
secrets = modal.Secret.from_name(SECRET_NAME)

_runner_src = Path(__file__).parent / "sandbox_runner.py"

# `standardwebhooks` backs `client.beta.webhooks.unwrap()` (the SDK's
# `[webhooks]` extra). Only the webhook image needs it — sandbox_runner.py
# never sees raw deliveries.
webhook_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("fastapi[standard]", "standardwebhooks", SDK_PACKAGE)
    .add_local_file(_runner_src, RUNNER_PATH, copy=True)
)

sandbox_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(SDK_PACKAGE)
    .add_local_file(_runner_src, RUNNER_PATH, copy=True)
)


@cache
def _client() -> anthropic.AsyncAnthropic:
    """Shared client for both webhook verification and the work poller.

    Lazy because ``modal deploy`` imports this module locally, where the
    secret env vars aren't set — constructing at module scope breaks deploy.
    """
    return anthropic.AsyncAnthropic(
        auth_token=os.environ["ANTHROPIC_ENVIRONMENT_KEY"],
        webhook_key=os.environ["ANTHROPIC_WEBHOOK_SECRET"],
    )


def _verify_webhook(
    client: anthropic.AsyncAnthropic, raw: bytes, headers: "Mapping[str, str]"
) -> UnwrapWebhookEvent:
    """``unwrap()`` is synchronous even on the async client — do not ``await``
    it. The ``whsec_`` secret is passed to ``webhook_key`` as-is: the SDK
    decodes its URL-safe base64 internally."""
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


async def _find_live_sandbox(key: str) -> modal.Sandbox | None:
    try:
        sb = await modal.Sandbox.from_name.aio(APP_NAME, name=key)
    except modal.exception.NotFoundError:
        return None
    return sb if await sb.poll.aio() is None else None


async def _create_sandbox(
    session_id: str,
    *,
    environment_id: str,
    work_id: str,
    environment_key: str,
    sandbox_timeout: int,
) -> modal.Sandbox:
    sb_app = await modal.App.lookup.aio(APP_NAME, create_if_missing=True)
    # Persist the whole workdir, not just outputs/, so the agent's working
    # tree and downloaded skills survive across sandbox lifetimes for the
    # same session. Mounted at /workspace so {workdir}/skills/<name>/ matches
    # what the agent's prompt and the other demos use.
    session_vol = modal.Volume.from_name(f"cma-session-{session_id}", create_if_missing=True)
    sb = await modal.Sandbox.create.aio(
        "python",
        RUNNER_PATH,
        app=sb_app,
        name=session_id,
        image=sandbox_image,
        timeout=sandbox_timeout,
        volumes={"/workspace": session_vol},
        # Same env contract as `ant beta:worker poll --on-work`: sandbox_runner.py
        # reads these to build the client and run EnvironmentWorker.handle_item().
        # ANTHROPIC_ENVIRONMENT_KEY is the runner's single credential.
        env={
            "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
            "ANTHROPIC_SESSION_ID": session_id,
            "ANTHROPIC_ENVIRONMENT_ID": environment_id,
            "ANTHROPIC_WORK_ID": work_id,
        },
    )
    await sb.set_tags.aio({"session_id": session_id})
    return sb


async def _process_work_item(
    *, session_id: str, work_id: str, environment_id: str, environment_key: str
) -> dict:
    """Get-or-create a Modal Sandbox for one already-ack'd work item.

    The poller has already ack'd the item. Raises on Modal API errors — the
    caller treats any raise as "skip this item and keep draining".
    """
    existing = await _find_live_sandbox(session_id)
    if existing is not None:
        print(
            f"[webhook] work={work_id} session={session_id} sandbox={existing.object_id} (live)",
            flush=True,
        )
        return {
            "session_id": session_id,
            "work_id": work_id,
            "sandbox_id": existing.object_id,
            "created": False,
        }

    sb = await _create_sandbox(
        session_id,
        environment_id=environment_id,
        work_id=work_id,
        environment_key=environment_key,
        sandbox_timeout=3600,
    )
    print(
        f"[webhook] work={work_id} session={session_id} sandbox={sb.object_id} (created)",
        flush=True,
    )
    return {
        "session_id": session_id,
        "work_id": work_id,
        "sandbox_id": sb.object_id,
        "created": True,
    }


async def _drain_work(client: anthropic.AsyncAnthropic, environment_id: str) -> list[dict]:
    """Drain the queue via the SDK poller, spawning a sandbox per work item.

    ``drain=True`` returns when the queue is empty (the webhook handler must
    respond, not loop forever). ``auto_stop=False`` because each item is
    handed off to a detached Modal Sandbox that owns ``/stop`` — the poller
    must not terminate the lease out from under it. Items the poller already
    ack'd that then fail to spawn are logged and skipped; they reclaim on the
    next webhook (``reclaim_older_than_ms``) once the lease lapses.
    """
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    spawned: list[dict] = []
    failed: list[dict] = []
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
            spawned.append(
                await _process_work_item(
                    session_id=session_id,
                    work_id=work.id,
                    environment_id=environment_id,
                    environment_key=environment_key,
                )
            )
        except Exception as e:
            # SDK/httpx/Modal exceptions can embed request context, so log
            # type only — never the message.
            detail = type(e).__name__
            print(
                f"[webhook] FAILED work={work.id} session={session_id}: {detail}",
                flush=True,
            )
            failed.append({"work_id": work.id, "session_id": session_id, "error": detail})
    if failed:
        print(
            f"[webhook] drain finished: spawned={len(spawned)} failed={len(failed)}",
            flush=True,
        )
    return spawned + failed


@app.function(image=webhook_image, secrets=[secrets])
@modal.fastapi_endpoint(method="POST")
async def webhook(request: Request) -> dict:
    raw = await request.body()
    client = _client()
    event = _verify_webhook(client, raw, request.headers)

    print(f"[webhook] event={event.data.type} session_id={event.data.id}", flush=True)
    if event.data.type != "session.status_run_started":
        return {"status": "ignored", "event_type": event.data.type}

    spawned = await _drain_work(client, os.environ["ANTHROPIC_ENVIRONMENT_ID"])
    return {"status": "ok", "event_type": event.data.type, "spawned": spawned}
