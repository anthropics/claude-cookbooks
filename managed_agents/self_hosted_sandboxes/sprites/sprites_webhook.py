"""Sprites analogue of daytona_webhook.py.

FastAPI app: receives the session.status_run_started webhook, drains the
environment work queue, and per item creates a Sprite
([sprites.dev](https://sprites.dev), Fly.io's stateful sandboxes) running the
provider-agnostic ``sandbox_runner.py``. Deploy this anywhere that can serve
HTTP and reach the Sprites API (Fly, Render, a VM, etc.).

The webhook is a wake-up signal only — each delivery drains *all* pending work
items, so a single arriving webhook recovers any earlier missed deliveries.

Sprites has no published SDK, so this talks its REST API directly (create,
filesystem write, exec). A Sprite is a full Linux environment, so
``beta_agent_toolset_20260401`` (bash/read/write/edit/glob/grep) works as-is.

Env on the orchestrator host:
  ANTHROPIC_WEBHOOK_SECRET, ANTHROPIC_BASE_URL,
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  SPRITES_API_KEY, SPRITES_API_URL (optional)
"""

import os
import re
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import anthropic
import httpx
from anthropic.types.beta import UnwrapWebhookEvent
from fastapi import FastAPI, HTTPException, Request

# Same provider-agnostic sandbox_runner.py the Modal and Daytona demos use.
RUNNER_SRC = (
    Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py"
).read_text()

SPRITES_API_URL = os.environ.get("SPRITES_API_URL", "https://api.sprites.dev")
WORKDIR = "/workspace"
RUNNER_PATH = "/root/sandbox_runner.py"

app = FastAPI()


# ---------------------------------------------------------------------------
# Minimal Sprites REST client (no SDK). Auth is a single bearer token.
# ---------------------------------------------------------------------------


@cache
def _sprites() -> httpx.Client:
    return httpx.Client(
        base_url=SPRITES_API_URL,
        headers={"authorization": f"Bearer {os.environ['SPRITES_API_KEY']}"},
        timeout=httpx.Timeout(300.0),
    )


def _shquote(value: str) -> str:
    """POSIX single-quote a value for a sourced env file."""
    return "'" + value.replace("'", "'\\''") + "'"


def _sprite_name(session_id: str) -> str:
    """A DNS-label-safe Sprite name derived from the session id."""
    slug = re.sub(r"[^a-z0-9]+", "-", session_id.lower()).strip("-")[:40]
    return f"claude-agent-{slug}" if slug else f"claude-agent-{os.urandom(4).hex()}"


def _exec(name: str, command: str, env: "Mapping[str, str] | None" = None) -> int:
    """Run ``bash -c <command>`` in the Sprite and return its exit code.

    Sprites streams exec output as ``[type][payload]`` frames terminated by an
    exit frame ``0x03 <code>``; for a blocking command we only need the exit
    code, which is the final byte.
    """
    params: list[tuple[str, str]] = [
        ("cmd", "bash"),
        ("cmd", "-c"),
        ("cmd", command),
    ]
    for key, value in (env or {}).items():
        params.append(("env", f"{key}={value}"))
    resp = _sprites().post(f"/v1/sprites/{name}/exec", params=params)
    resp.raise_for_status()
    body = resp.content
    return body[-1] if len(body) >= 2 and body[-2] == 0x03 else 0


def _find_live(session_id: str) -> str | None:
    """Return the Sprite name if one for this session already exists and runs."""
    name = _sprite_name(session_id)
    resp = _sprites().get(f"/v1/sprites/{name}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return name if resp.json().get("status") in ("running", "warm") else None


def _spawn(
    session_id: str, *, environment_id: str, work_id: str, environment_key: str
) -> str:
    """Create a Sprite and start sandbox_runner.py inside it as a service.

    The runner is launched as a Sprite **service** rather than a detached
    `nohup ... &`: Sprites reaps an exec's process tree when the request
    connection closes, so a backgrounded process would not survive. Services are
    supervised and outlive the request. The runner self-stops its service on
    exit so the one-shot worker is not restarted after the session completes.
    """
    name = _sprite_name(session_id)
    # 201 created, or 409 if a Sprite with this name already exists (reuse it).
    created = _sprites().post(
        "/v1/sprites", json={"name": name, "wait_for_capacity": True}
    )
    if created.status_code not in (200, 201, 409):
        created.raise_for_status()

    _sprites().put(
        f"/v1/sprites/{name}/fs/write",
        params={"path": RUNNER_PATH},
        content=RUNNER_SRC.encode(),
        headers={"content-type": "application/octet-stream"},
    ).raise_for_status()

    # The runner needs the SDK and the WORKDIR. (Pre-bake these into a Sprite
    # checkpoint for production to drop the ~10-15s cold-start install.)
    code = _exec(
        name, f"mkdir -p {WORKDIR} && python3 -m pip install -q anthropic"
    )
    if code != 0:
        raise RuntimeError(f"sprite {name}: runner setup failed (exit {code})")

    # Same env contract as `ant beta:worker poll --on-work`: sandbox_runner.py
    # reads these to build the client and run the worker's handle_item().
    # ANTHROPIC_ENVIRONMENT_KEY is the runner's single credential — the org API
    # key never reaches the Sprite. Written to a file (not service args) so the
    # key never appears in process listings.
    env = {
        "ANTHROPIC_BASE_URL": os.environ.get(
            "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
        ),
        "ANTHROPIC_ENVIRONMENT_KEY": environment_key,
        "ANTHROPIC_SESSION_ID": session_id,
        "ANTHROPIC_ENVIRONMENT_ID": environment_id,
        "ANTHROPIC_WORK_ID": work_id,
    }
    env_file = "\n".join(f"{k}={_shquote(v)}" for k, v in env.items()) + "\n"
    _sprites().put(
        f"/v1/sprites/{name}/fs/write",
        params={"path": "/root/runner.env"},
        content=env_file.encode(),
        headers={"content-type": "application/octet-stream"},
    ).raise_for_status()

    # Service supervises the runner; it self-stops on exit so the one-shot
    # worker isn't restarted. Service stdout/stderr land in
    # /.sprite/logs/services/agent-runner.log inside the Sprite.
    runner_cmd = (
        "set -a; . /root/runner.env; set +a; "
        f"python3 {RUNNER_PATH}; "
        "sprite-env services stop agent-runner >/dev/null 2>&1 || true"
    )
    _sprites().put(
        f"/v1/sprites/{name}/services/agent-runner",
        json={"cmd": "bash", "args": ["-lc", runner_cmd]},
    ).raise_for_status()
    return name


# ---------------------------------------------------------------------------
# Webhook + work queue (identical flow to the Daytona / Modal demos).
# ---------------------------------------------------------------------------


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
            existing = _find_live(session_id)
            if existing is not None:
                print(
                    f"[webhook] work={work.id} session={session_id} sprite={existing} (live)",
                    flush=True,
                )
                spawned.append(
                    {
                        "session_id": session_id,
                        "work_id": work.id,
                        "sprite": existing,
                        "created": False,
                    }
                )
                continue
            name = _spawn(
                session_id,
                environment_id=environment_id,
                work_id=work.id,
                environment_key=environment_key,
            )
            print(
                f"[webhook] work={work.id} session={session_id} sprite={name} (created)",
                flush=True,
            )
            spawned.append(
                {
                    "session_id": session_id,
                    "work_id": work.id,
                    "sprite": name,
                    "created": True,
                }
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
