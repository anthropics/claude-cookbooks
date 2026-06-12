"""Tenki Sandbox analogue of modal_sandbox_webhook.py.

FastAPI app: receives the session.status_run_started webhook, drains the
environment work queue, and per item creates or reuses a Tenki Sandbox running
the provider-agnostic ``sandbox_runner.py``. Deploy this anywhere that can
serve HTTP and reach the Tenki API.

The webhook is a wake-up signal only — each delivery drains *all* pending work
items, so a single arriving webhook recovers any earlier missed deliveries.

Env on the orchestrator host:
  ANTHROPIC_WEBHOOK_SECRET, ANTHROPIC_BASE_URL,
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  TENKI_AUTH_TOKEN or TENKI_API_KEY, TENKI_API_ENDPOINT,
  TENKI_PROJECT_ID, TENKI_SANDBOX_IMAGE
"""

import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import anthropic
from anthropic.types.beta import UnwrapWebhookEvent
from fastapi import FastAPI, HTTPException, Request
from tenki_sandbox import Client as TenkiClient
from tenki_sandbox import Sandbox as TenkiSandbox

SDK_PACKAGE = "anthropic"
WORKDIR = "/workspace"
RUNNER_PATH = f"{WORKDIR}/sandbox_runner.py"
RUNNER_LOG = f"{WORKDIR}/anthropic-runner.log"
RUNNER_SRC = (Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py").read_text()

app = FastAPI()


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


@cache
def _tenki_client() -> TenkiClient:
    """Tenki client, lazy so imports do not require deploy-time env vars."""
    return TenkiClient()


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


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _env_int(name: str, default: int) -> int:
    value = _optional_env(name)
    return default if value is None else int(value)


def _env_int_optional(name: str) -> int | None:
    value = _optional_env(name)
    return None if value is None else int(value)


def _env_bool(name: str, default: bool = False) -> bool:
    value = _optional_env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _session_tag(session_id: str) -> str:
    return f"anthropic-session:{session_id.lower()}"


def _find_sandbox(session_id: str) -> TenkiSandbox | None:
    """Return a running Tenki Sandbox for the Anthropic session, if any."""
    client = _tenki_client()
    for sandbox in client.list(tags=[_session_tag(session_id)]):
        if sandbox.state == "RUNNING":
            return sandbox
        if sandbox.state == "PAUSED":
            sandbox.resume()
            sandbox.wait_ready(_env_int("TENKI_SANDBOX_RESUME_TIMEOUT_SECONDS", 180))
            return sandbox
    return None


def _create_sandbox(session_id: str, *, environment_id: str, work_id: str) -> TenkiSandbox:
    """Create a Tenki Sandbox tagged for idempotent session reuse."""
    create_kwargs = {
        "name": f"anthropic-session-{session_id}",
        "project_id": _optional_env("TENKI_PROJECT_ID"),
        "image": _optional_env("TENKI_SANDBOX_IMAGE"),
        "tags": [_session_tag(session_id)],
        "metadata": {
            "anthropic_environment_id": environment_id,
            "anthropic_session_id": session_id,
            "anthropic_work_id": work_id,
        },
        "max_duration": _env_int("TENKI_SANDBOX_MAX_DURATION_SECONDS", 3600),
        "idle_timeout_minutes": _env_int("TENKI_SANDBOX_IDLE_TIMEOUT_MINUTES", 30),
        "pause_retention": _env_int("TENKI_SANDBOX_PAUSE_RETENTION_SECONDS", 24 * 3600),
        "sticky": _env_bool("TENKI_SANDBOX_STICKY"),
    }
    for key, env_name in {
        "cpu_cores": "TENKI_SANDBOX_CPU_CORES",
        "memory_mb": "TENKI_SANDBOX_MEMORY_MB",
        "disk_size_gb": "TENKI_SANDBOX_DISK_SIZE_GB",
    }.items():
        value = _env_int_optional(env_name)
        if value is not None:
            create_kwargs[key] = value

    return _tenki_client().create(**create_kwargs)


def _runner_is_active(sandbox: TenkiSandbox) -> bool:
    try:
        result = sandbox.shell(
            "ps -eo args | grep -F '[s]andbox_runner.py' >/dev/null",
            timeout=10,
        )
    except Exception as e:
        print(
            f"[webhook] runner status check failed sandbox={sandbox.id}: {type(e).__name__}",
            flush=True,
        )
        return False
    return result.exit_code == 0


def _install_runner(sandbox: TenkiSandbox) -> None:
    sandbox.fs.mkdir(WORKDIR, recursive=True)
    sandbox.fs.write_text(RUNNER_PATH, RUNNER_SRC)
    sandbox.shell(
        f"python3 -c 'import {SDK_PACKAGE}' 2>/dev/null || python3 -m pip install -q {SDK_PACKAGE}",
        timeout=180,
        check=True,
    )


def _start_runner(
    sandbox: TenkiSandbox,
    session_id: str,
    *,
    environment_id: str,
    work_id: str,
    environment_key: str,
) -> None:
    """Upload the worker and start it detached inside the Tenki Sandbox."""
    _install_runner(sandbox)
    sandbox.shell(
        f"nohup python3 {RUNNER_PATH} >{RUNNER_LOG} 2>&1 &",
        env={
            "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
            "ANTHROPIC_SESSION_ID": session_id,
            "ANTHROPIC_ENVIRONMENT_ID": environment_id,
            "ANTHROPIC_WORK_ID": work_id,
        },
        timeout=30,
        check=True,
    )


def _process_work_item(
    *, session_id: str, work_id: str, environment_id: str, environment_key: str
) -> dict:
    """Get-or-create a Tenki Sandbox for one already-ack'd work item."""
    sandbox = _find_sandbox(session_id)
    if sandbox is not None:
        if _runner_is_active(sandbox):
            print(
                f"[webhook] work={work_id} session={session_id} sandbox={sandbox.id} (live)",
                flush=True,
            )
            return {
                "session_id": session_id,
                "work_id": work_id,
                "sandbox_id": sandbox.id,
                "created": False,
                "runner_started": False,
            }
        _start_runner(
            sandbox,
            session_id,
            environment_id=environment_id,
            work_id=work_id,
            environment_key=environment_key,
        )
        print(
            f"[webhook] work={work_id} session={session_id} sandbox={sandbox.id} (reused)",
            flush=True,
        )
        return {
            "session_id": session_id,
            "work_id": work_id,
            "sandbox_id": sandbox.id,
            "created": False,
            "runner_started": True,
        }

    sandbox = _create_sandbox(session_id, environment_id=environment_id, work_id=work_id)
    _start_runner(
        sandbox,
        session_id,
        environment_id=environment_id,
        work_id=work_id,
        environment_key=environment_key,
    )
    print(
        f"[webhook] work={work_id} session={session_id} sandbox={sandbox.id} (created)",
        flush=True,
    )
    return {
        "session_id": session_id,
        "work_id": work_id,
        "sandbox_id": sandbox.id,
        "created": True,
        "runner_started": True,
    }


async def _drain_work(client: anthropic.AsyncAnthropic, environment_id: str) -> list[dict]:
    """Drain the queue via the SDK poller, spawning a sandbox per work item.

    ``client.beta.environments.work.poller`` is the user-facing entry point: it
    builds a scoped sub-client from the environment key and yields each ack'd
    work item. It is async-only (lives on ``AsyncWork``). ``drain=True`` returns
    when the queue is empty (the webhook handler must respond, not loop forever).
    ``auto_stop=False`` because each item is handed off to a detached Tenki
    Sandbox that owns ``/stop`` — the poller must not terminate the lease out
    from under it.
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
                _process_work_item(
                    session_id=session_id,
                    work_id=work.id,
                    environment_id=environment_id,
                    environment_key=environment_key,
                )
            )
        except Exception as e:
            # SDK/httpx/Tenki exceptions can embed request context, so log
            # type only — never the message.
            detail = type(e).__name__
            print(
                f"[webhook] FAILED work={work.id} session={session_id}: {detail}",
                flush=True,
            )
            failed.append({"session_id": session_id, "work_id": work.id, "error": detail})
    return spawned + failed


@app.post("/")
async def webhook(request: Request) -> dict:
    raw = await request.body()
    client = _client()
    event = _verify_webhook(client, raw, request.headers)

    if event.data.type != "session.status_run_started":
        return {"status": "ignored", "event_type": event.data.type}

    spawned = await _drain_work(client, os.environ["ANTHROPIC_ENVIRONMENT_ID"])
    return {"status": "ok", "event_type": event.data.type, "spawned": spawned}
