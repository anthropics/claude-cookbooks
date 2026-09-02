"""
AgentCore Runtime entrypoint for the Anthropic CMA self-hosted sandbox.

Each invoke_agent_runtime call lands here with session affinity guaranteed by
the runtimeSessionId, so this microVM owns one Anthropic session for its
lifetime. The host-side `ant beta:worker poll --on-work` claims a work item
from Anthropic CMA, then calls invoke_agent_runtime with the work payload.
This handler spawns `ant beta:worker run` to attach to the session's event
stream, execute tool calls in /workspace, and exit when the session idles.
"""

import os
import subprocess
import sys

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

WORKDIR = os.environ.get("AGENT_WORKDIR", "/workspace")
ANT_BIN = os.environ.get("ANT_BIN", "/usr/local/bin/ant")
MAX_IDLE = os.environ.get("ANT_MAX_IDLE", "60s")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")


@app.entrypoint
def handler(payload, context):
    required = ("session_id", "work_id", "environment_id", "environment_key")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return {"error": f"missing fields in payload: {missing}"}

    env = {
        **os.environ,
        "ANTHROPIC_SESSION_ID": payload["session_id"],
        "ANTHROPIC_WORK_ID": payload["work_id"],
        "ANTHROPIC_ENVIRONMENT_ID": payload["environment_id"],
        "ANTHROPIC_ENVIRONMENT_KEY": payload["environment_key"],
        "ANTHROPIC_AUTH_TOKEN": payload["environment_key"],
        "ANTHROPIC_BASE_URL": payload.get("base_url", BASE_URL),
    }

    print(
        f"[server] runtimeSessionId={getattr(context, 'session_id', None)} "
        f"anthropicSessionId={payload['session_id']} "
        f"workId={payload['work_id']}",
        flush=True,
    )

    result = subprocess.run(  # noqa: S603 - all argv values are env-controlled, not user input
        [
            ANT_BIN,
            "beta:worker",
            "run",
            "--workdir",
            WORKDIR,
            "--unrestricted-paths",
            "--max-idle",
            MAX_IDLE,
            "--log-format",
            "json",
        ],
        env=env,
        cwd=WORKDIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    return {
        "session_id": payload["session_id"],
        "work_id": payload["work_id"],
        "exit_code": result.returncode,
    }


if __name__ == "__main__":
    app.run()
