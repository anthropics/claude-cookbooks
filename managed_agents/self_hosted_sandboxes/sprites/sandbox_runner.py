"""Runs inside the Sprite.

``client.beta.environments.work.worker(...).handle_item()`` is the whole runner:
it builds the per-session ``AgentToolContext`` at ``workdir`` and downloads the
agent's skills into ``{workdir}/skills/<name>/``, then runs a
``SessionToolRunner`` (heartbeat + reconcile + event stream + tool dispatch +
result posting) for the session, and force-stops the work item on exit. With no
per-item arguments it reads the same ``ANTHROPIC_*`` env vars
``ant beta:worker poll --on-work`` sets, which the agent-runner service sources
from ``/root/runner.env`` (written by the worker that created the Sprite and
deleted right after sourcing).

Idle policy is the SDK default: the runner stays alive for as long as the
session has activity and exits ``DEFAULT_MAX_IDLE`` (60s) after
``session.status_idle`` with ``stop_reason: end_turn``; any other event —
including ``requires_action`` idle, where the agent is blocked on the sandbox —
resets the clock.

Env vars (sourced from ``/root/runner.env``):
  ANTHROPIC_BASE_URL        - API base URL
  ANTHROPIC_ENVIRONMENT_KEY - the environment key: the worker's single
                              credential. Authenticates the client (skill
                              download) and, threaded through the worker,
                              every poll / heartbeat / event-stream / force-stop
                              call.
  ANTHROPIC_SESSION_ID      - session id
  ANTHROPIC_ENVIRONMENT_ID  - environment id
  ANTHROPIC_WORK_ID         - work item id
"""

import asyncio
import logging
import os
import sys

from anthropic import AsyncAnthropic

# EnvironmentWorker reports lifecycle (start, idle-out, heartbeat shutdown,
# stream reconnects, tool dispatch) at INFO via stdlib logging. Without a
# handler that's all silently dropped — and the exit reason is the only
# diagnostic this process emits, so route it to stdout, which the service
# supervisor captures in /.sprite/logs/services/agent-runner.log.
logging.basicConfig(
    level=logging.INFO,
    format="[runner] %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

WORKDIR = "/workspace"


async def main() -> None:
    # The environment key is the only credential: the client uses it (skill
    # download), and the worker threads it through every poll / heartbeat /
    # event-stream / force-stop call. base_url from ANTHROPIC_BASE_URL.
    environment_key = os.environ["ANTHROPIC_ENVIRONMENT_KEY"]
    async with AsyncAnthropic(auth_token=environment_key) as client:
        await client.beta.environments.work.worker(
            environment_key=environment_key,
            workdir=WORKDIR,
            unrestricted_paths=True,
        ).handle_item()


if __name__ == "__main__":
    asyncio.run(main())
