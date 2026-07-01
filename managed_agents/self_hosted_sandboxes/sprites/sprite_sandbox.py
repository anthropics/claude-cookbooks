"""Sprite spawn helper shared by the webhook and always-on poller demos.

Creates a Sprite ([sprites.dev](https://sprites.dev), Fly.io's stateful
sandboxes) and starts the provider-agnostic ``sandbox_runner.py`` inside it.
Sprites has no published SDK, so this talks its REST API directly (create,
filesystem write, exec, services) — the only dependency is ``httpx``.

The runner is launched as a Sprite **service** rather than a detached
``nohup ... &``: Sprites reaps an exec's process tree when the request
connection closes, so a backgrounded process would not survive. Services are
supervised and outlive the request; the runner self-stops its service on exit so
the one-shot worker is not restarted after the session completes.

Env:
  SPRITE_TOKEN               - Sprites API token (org-slug/org-id/token-id/token-value)
  SPRITES_API_URL (optional) - defaults to https://api.sprites.dev
"""

import os
import re
from collections.abc import Mapping
from functools import cache
from pathlib import Path

import httpx

# Same provider-agnostic sandbox_runner.py the Modal and Daytona demos use.
RUNNER_SRC = (
    Path(__file__).resolve().parent.parent / "modal" / "sandbox_runner.py"
).read_text()

SPRITES_API_URL = os.environ.get("SPRITES_API_URL", "https://api.sprites.dev")
WORKDIR = "/workspace"
RUNNER_PATH = "/root/sandbox_runner.py"


@cache
def _sprites() -> httpx.Client:
    return httpx.Client(
        base_url=SPRITES_API_URL,
        headers={"authorization": f"Bearer {os.environ['SPRITE_TOKEN']}"},
        timeout=httpx.Timeout(300.0),
    )


def _shquote(value: str) -> str:
    """POSIX single-quote a value for a sourced env file."""
    return "'" + value.replace("'", "'\\''") + "'"


def sprite_name(session_id: str) -> str:
    """A DNS-label-safe Sprite name derived from the session id."""
    slug = re.sub(r"[^a-z0-9]+", "-", session_id.lower()).strip("-")[:40]
    return f"claude-agent-{slug}" if slug else f"claude-agent-{os.urandom(4).hex()}"


def _exec(name: str, command: str, env: "Mapping[str, str] | None" = None) -> int:
    """Run ``bash -c <command>`` in the Sprite and return its exit code.

    Sprites streams exec output as ``[type][payload]`` frames terminated by an
    exit frame ``0x03 <code>``; for a blocking command we only need the exit
    code, which is the final byte.
    """
    params: list[tuple[str, str]] = [("cmd", "bash"), ("cmd", "-c"), ("cmd", command)]
    for key, value in (env or {}).items():
        params.append(("env", f"{key}={value}"))
    resp = _sprites().post(f"/v1/sprites/{name}/exec", params=params)
    resp.raise_for_status()
    body = resp.content
    return body[-1] if len(body) >= 2 and body[-2] == 0x03 else 0


def find_live(session_id: str) -> str | None:
    """Return the Sprite name if one for this session already exists and runs."""
    name = sprite_name(session_id)
    resp = _sprites().get(f"/v1/sprites/{name}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return name if resp.json().get("status") in ("running", "warm") else None


def spawn(
    session_id: str, *, environment_id: str, work_id: str, environment_key: str
) -> str:
    """Create a Sprite and start sandbox_runner.py inside it as a service."""
    name = sprite_name(session_id)
    # Tolerate the Sprite already existing (reuse it).
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
    code = _exec(name, f"mkdir -p {WORKDIR} && python3 -m pip install -q anthropic")
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

    # The service supervises the runner but does not hold the Sprite active:
    # once the session is underway the runner only makes outbound calls, so the
    # Sprite would pause after its short (~30s) idle window and stall a long
    # session mid-turn. A Task holds it open. We register one, refresh it on a
    # heartbeat comfortably shorter than its expiry (max 1h), then kill the
    # heartbeat and delete the task when the runner exits. If the runner instead
    # crashes, the task expires on its own and the Sprite is free to pause (the
    # crash-safety net; see keeping-sprites-running). `sprite-env curl` is the
    # in-Sprite shorthand for the Tasks API on the management socket. The service
    # self-stops on exit so the one-shot worker isn't restarted; its
    # stdout/stderr land in /.sprite/logs/services/agent-runner.log.
    runner_cmd = (
        "set -a; . /root/runner.env; set +a\n"
        """sprite-env curl -X POST /v1/tasks -d '{"name": "agent-runner", "expire": "5m"}' >/dev/null 2>&1\n"""
        """( while true; do sprite-env curl -X PUT /v1/tasks/agent-runner -d '{"expire": "5m"}' >/dev/null 2>&1; sleep 60; done ) &\n"""
        "heartbeat=$!\n"
        f"python3 {RUNNER_PATH}\n"
        'kill "$heartbeat" 2>/dev/null || true\n'
        "sprite-env curl -X DELETE /v1/tasks/agent-runner >/dev/null 2>&1 || true\n"
        "sprite-env services stop agent-runner >/dev/null 2>&1 || true"
    )
    _sprites().put(
        f"/v1/sprites/{name}/services/agent-runner",
        json={"cmd": "bash", "args": ["-lc", runner_cmd]},
    ).raise_for_status()
    return name
