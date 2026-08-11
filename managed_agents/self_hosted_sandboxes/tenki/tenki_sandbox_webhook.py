"""FastAPI webhook for running Anthropic Managed Agents in Tenki sandboxes."""

import os
from collections.abc import Mapping
from contextlib import asynccontextmanager
from functools import cache
from pathlib import Path

import anthropic
import tenki
from anthropic.types.beta import UnwrapWebhookEvent
from fastapi import FastAPI, HTTPException, Request

SDK_PACKAGE = "anthropic"
WORKDIR = "workspace"
RUNNER_PATH = f"{WORKDIR}/sandbox_runner.py"
RUNNER_LOG = f"{WORKDIR}/anthropic-runner.log"
RUNNER_SRC = (Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py").read_text()


@cache
def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        auth_token=os.environ["ANTHROPIC_ENVIRONMENT_KEY"],
        webhook_key=os.environ["ANTHROPIC_WEBHOOK_SECRET"],
    )


@cache
def _tenki_client() -> tenki.AsyncClient:
    return tenki.AsyncClient()


@asynccontextmanager
async def _lifespan(_: FastAPI):
    yield
    if _tenki_client.cache_info().currsize:
        client = _tenki_client()
        _tenki_client.cache_clear()
        await client.close()
    if _client.cache_info().currsize:
        client = _client()
        _client.cache_clear()
        await client.close()


app = FastAPI(lifespan=_lifespan)


def _verify_webhook(
    client: anthropic.AsyncAnthropic, raw: bytes, headers: "Mapping[str, str]"
) -> UnwrapWebhookEvent:
    from standardwebhooks import WebhookVerificationError

    try:
        return client.beta.webhooks.unwrap(raw.decode(), headers=headers)
    except (WebhookVerificationError, KeyError) as e:
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


async def _find_sandbox(session_id: str) -> tenki.AsyncSandbox | None:
    client = _tenki_client()
    for sandbox in await client.list(tags=[_session_tag(session_id)]):
        if sandbox.state == "RUNNING":
            return sandbox
        if sandbox.state == "PAUSED":
            await sandbox.resume()
            await sandbox.wait_ready(_env_int("TENKI_SANDBOX_RESUME_TIMEOUT_SECONDS", 180))
            return sandbox
    return None


async def _create_sandbox(
    session_id: str, *, environment_id: str, work_id: str
) -> tenki.AsyncSandbox:
    create_kwargs = {
        "name": f"anthropic-session-{session_id}",
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

    return await _tenki_client().create(**create_kwargs)


async def _runner_is_active(sandbox: tenki.AsyncSandbox) -> bool:
    try:
        result = await sandbox.shell(
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


async def _install_runner(sandbox: tenki.AsyncSandbox) -> None:
    await sandbox.fs.mkdir(WORKDIR, recursive=True)
    await sandbox.fs.write_text(RUNNER_PATH, RUNNER_SRC)
    await sandbox.shell(
        f"python3 -c 'import {SDK_PACKAGE}' 2>/dev/null || python3 -m pip install -q {SDK_PACKAGE}",
        timeout=180,
        check=True,
    )


async def _start_runner(
    sandbox: tenki.AsyncSandbox,
    session_id: str,
    *,
    environment_id: str,
    work_id: str,
    environment_key: str,
) -> None:
    await _install_runner(sandbox)
    await sandbox.shell(
        f"nohup python3 {RUNNER_PATH} >{RUNNER_LOG} 2>&1 &",
        env={
            "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
            "ANTHROPIC_SESSION_ID": session_id,
            "ANTHROPIC_ENVIRONMENT_ID": environment_id,
            "ANTHROPIC_WORK_ID": work_id,
            "ANTHROPIC_WORKDIR": WORKDIR,
        },
        timeout=30,
        check=True,
    )


async def _process_work_item(
    *, session_id: str, work_id: str, environment_id: str, environment_key: str
) -> dict:
    sandbox = await _find_sandbox(session_id)
    if sandbox is not None:
        if await _runner_is_active(sandbox):
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
        await _start_runner(
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

    sandbox = await _create_sandbox(session_id, environment_id=environment_id, work_id=work_id)
    await _start_runner(
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
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    spawned: list[dict] = []
    failed: list[dict] = []
    async for work in client.beta.environments.work.poller(
        environment_id=environment_id,
        environment_key=environment_key,
        block_ms=None,
        reclaim_older_than_ms=2000,
        drain=True,
        # The detached sandbox owns the lease, so the host poller must not stop it.
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
