"""Sprites self-hosted sandbox demo — always-on poller variant.

A long-running process that polls the environment work queue continuously and,
per claimed session, creates a Sprite running the provider-agnostic
``sandbox_runner.py`` (see ``sprite_sandbox.spawn``). This is the
[always-on](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes#always-on-sdk)
alternative to ``sprites_webhook.py``: no public HTTP endpoint, only outbound
HTTPS.

Unlike ``EnvironmentWorker`` (which runs tools in-process), this drives the
lower-level ``work.poller`` so each session runs in its own Sprite. ``drain`` is
omitted, so the poller blocks for new work indefinitely; ``auto_stop=False``
because each item is handed to a detached Sprite that owns ``/stop``.

No org API key reaches the runner: the poller and each Sprite authenticate with
the environment key — the single credential for both the control plane and the
per-session calls.

Env:
  ANTHROPIC_ENVIRONMENT_ID, ANTHROPIC_ENVIRONMENT_KEY,
  ANTHROPIC_BASE_URL (optional),
  SPRITE_TOKEN, SPRITES_API_URL (optional)
"""

import asyncio
import os
import signal

import anthropic

from sprite_sandbox import find_live, spawn


async def main() -> None:
    environment_id = os.environ["ANTHROPIC_ENVIRONMENT_ID"]
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    client = anthropic.AsyncAnthropic(auth_token=environment_key)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    print("[poller] polling environment work queue (Ctrl-C to stop)…", flush=True)
    async for work in client.beta.environments.work.poller(
        environment_id=environment_id,
        environment_key=environment_key,
        reclaim_older_than_ms=2000,
        auto_stop=False,  # drain omitted -> block for new work indefinitely
    ):
        if stop.is_set():
            break
        if work.data.type != "session":
            print(f"[poller] skipping work={work.id} type={work.data.type}", flush=True)
            continue
        session_id = work.data.id
        try:
            name = find_live(session_id) or spawn(
                session_id,
                environment_id=environment_id,
                work_id=work.id,
                environment_key=environment_key,
            )
            print(f"[poller] work={work.id} session={session_id} sprite={name}", flush=True)
        except Exception as e:
            print(
                f"[poller] FAILED work={work.id} session={session_id}: {type(e).__name__}",
                flush=True,
            )

    print("[poller] stopped", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
