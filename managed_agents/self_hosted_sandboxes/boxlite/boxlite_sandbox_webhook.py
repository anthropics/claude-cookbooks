"""BoxLite analogue of modal_sandbox_webhook.py / daytona_webhook.py.

FastAPI app: receives the session.status_run_started webhook, drains the
environment work queue, and per item creates a BoxLite microVM running the
provider-agnostic ``sandbox_runner.py``. Deploy this anywhere that can serve
HTTP and reach the operator's ``boxlite serve`` instance (Fly, Render, a VM,
or the same host as ``boxlite serve``).

The webhook is a wake-up signal only — each delivery drains *all* pending work
items, so a single arriving webhook recovers any earlier missed deliveries.

Env on the orchestrator host:
  ANTHROPIC_WEBHOOK_SECRET, ANTHROPIC_BASE_URL,
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  BOXLITE_REST_URL (default http://localhost:8100),
  BOXLITE_API_KEY  (default local-dev-key — the bearer the reference
                    ``boxlite serve`` configuration accepts)
"""

import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import anthropic
from anthropic.types.beta import UnwrapWebhookEvent
from boxlite import ApiKeyCredential, Boxlite, BoxliteRestOptions, BoxOptions
from fastapi import FastAPI, HTTPException, Request

SDK_PACKAGE = "anthropic"
IMAGE = "python:3.12-slim"

# Same provider-agnostic sandbox_runner.py the Modal demo ships. We read it
# from the sibling modal/ directory rather than vendoring a copy here, so the
# two variants can't drift.
RUNNER_SRC_PATH = str(
    (Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py").resolve()
)

# Where the runner lands inside the microVM. Matches Daytona/Modal's
# /root/sandbox_runner.py convention.
RUNNER_PATH_IN_BOX = "/root/sandbox_runner.py"

app = FastAPI()


@cache
def _runtime() -> Boxlite:
    """REST client for the operator's ``boxlite serve``.

    BOXLITE_REST_URL points at wherever the operator runs ``boxlite serve``;
    BOXLITE_API_KEY is the bearer that server is configured to accept (the
    reference server accepts ``local-dev-key``).
    """
    return Boxlite.rest(
        BoxliteRestOptions(
            url=os.environ.get("BOXLITE_REST_URL", "http://localhost:8100"),
            credential=ApiKeyCredential(
                os.environ.get("BOXLITE_API_KEY", "local-dev-key"),
            ),
        )
    )


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


def _box_name(session_id: str) -> str:
    return f"anthropic-session-{session_id}"


async def _find_live(rt: Boxlite, session_id: str) -> str | None:
    """Return the id of a running BoxLite microVM for this session, if any.

    Matches Daytona's _find_live: a duplicate work item for a session that
    already has a live runner is a no-op (the existing runner will pick up
    the new session events via the SSE stream).
    """
    name = _box_name(session_id)
    for info in await rt.list_info():
        if info.name == name and info.state.status == "running":
            return info.id
    return None


async def _spawn(
    rt: Boxlite,
    session_id: str,
    *,
    environment_id: str,
    work_id: str,
    environment_key: str,
) -> str:
    """Create a BoxLite microVM and start sandbox_runner.py inside it (detached).

    copy_in MUST run before start() — the REST `Box.copy_in` extracts files
    into the rootfs layer, which is sealed once the microVM boots. See
    https://github.com/boxlite-ai/boxlite/blob/main/examples/python/08_rest_api/copy_files.py.
    """
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    box = await rt.create(
        BoxOptions(image=IMAGE, auto_remove=False),
        name=_box_name(session_id),
    )

    # copy_in before start: rootfs-layer injection.
    await box.copy_in(RUNNER_SRC_PATH, RUNNER_PATH_IN_BOX)
    await box.start()

    # Install the SDK at runtime so the cookbook stays minimal (no Dockerfile).
    # Production deployments should pre-bake `anthropic` into a custom image
    # and skip this step. Adds ~5-10 s of cold-start latency per session.
    prep = await box.exec(
        "pip",
        args=["install", "--no-cache-dir", "-q", SDK_PACKAGE],
    )
    prep_result = await prep.wait()
    if prep_result.exit_code != 0:
        raise RuntimeError(f"runner dep install failed (exit={prep_result.exit_code})")

    # Detach: nohup + & so the shell exits immediately. The microVM's init
    # keeps the python runner alive after this exec returns. Matches the
    # Daytona variant's `nohup ... >/tmp/runner.log 2>&1 &` pattern.
    #
    # Same env contract as `ant beta:worker poll --on-work`: sandbox_runner.py
    # reads these to build the client and run the worker's handle_item().
    # ANTHROPIC_ENVIRONMENT_KEY is the runner's single credential.
    runner = await box.exec(
        "sh",
        args=[
            "-c",
            f"nohup python {RUNNER_PATH_IN_BOX} > /tmp/runner.log 2>&1 &",
        ],
        env=[
            ("ANTHROPIC_BASE_URL", base_url),
            ("ANTHROPIC_ENVIRONMENT_KEY", environment_key),
            ("ANTHROPIC_SESSION_ID", session_id),
            ("ANTHROPIC_ENVIRONMENT_ID", environment_id),
            ("ANTHROPIC_WORK_ID", work_id),
        ],
    )
    await runner.wait()  # returns ~instantly: the shell exits after backgrounding.
    return box.id


async def _drain_work(client: anthropic.AsyncAnthropic, environment_id: str) -> list[dict]:
    """Drain the queue via the SDK poller, spawning a microVM per work item.

    ``client.beta.environments.work.poller`` is the user-facing entry point:
    it builds a scoped sub-client from the environment key and yields each
    ack'd work item. It is async-only (lives on ``AsyncWork``). ``drain=True``
    returns when the queue is empty (the webhook handler must respond, not
    loop forever). ``auto_stop=False`` because each item is handed off to a
    detached BoxLite microVM that owns ``/stop`` — the poller must not
    terminate the lease out from under it.
    """
    rt = _runtime()
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
            existing = await _find_live(rt, session_id)
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
            sandbox_id = await _spawn(
                rt,
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
            # SDK / BoxLite exceptions can embed request context, so log type
            # only — never the message body.
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
