#!/usr/bin/env bash
# Host-side launcher for the AgentCore variant of the CMA self-hosted sandbox.
#
# Runs `ant beta:worker poll` on the host, with --on-work pointed at a Python
# bridge that calls invoke_agent_runtime per claimed work item. AgentCore
# Runtime's session affinity (runtimeSessionId == ANTHROPIC_SESSION_ID) maps
# one Anthropic session to one microVM, exactly the same shape as the docker
# variant's per-session container.
#
# Requires:
#   - `ant` on PATH (install snippet in README.md)
#   - python3 with boto3 + AWS creds for the deployed AgentCore runtime
#   - AgentCore runtime already deployed (see deploy.py)
#
# Env:
#   ANTHROPIC_ENVIRONMENT_ID    self-hosted environment id (env_...)
#   ANTHROPIC_ENVIRONMENT_KEY   environment key (sk-ant-oat...)
#   AGENTCORE_RUNTIME_ARN       runtime ARN from deploy.py
#   AGENTCORE_REGION            optional, default us-west-2
set -euo pipefail
cd "$(dirname "$0")"

: "${ANTHROPIC_ENVIRONMENT_ID:?set ANTHROPIC_ENVIRONMENT_ID (env_...)}"
: "${ANTHROPIC_ENVIRONMENT_KEY:?set ANTHROPIC_ENVIRONMENT_KEY (sk-ant-oat...)}"
: "${AGENTCORE_RUNTIME_ARN:?set AGENTCORE_RUNTIME_ARN (run deploy.py first)}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
export AGENTCORE_REGION="${AGENTCORE_REGION:-us-west-2}"

command -v ant >/dev/null || {
  echo "ant not found on PATH. Install the pinned build (see README.md)." >&2
  exit 1
}
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }

echo "[start] polling env=${ANTHROPIC_ENVIRONMENT_ID} runtime=${AGENTCORE_RUNTIME_ARN}"
exec ant beta:worker poll \
  --on-work "$PWD/on-work.sh" \
  --workdir /tmp \
  --log-format json
