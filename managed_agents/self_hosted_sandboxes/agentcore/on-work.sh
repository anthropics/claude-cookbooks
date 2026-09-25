#!/usr/bin/env bash
# Thin wrapper invoked by `ant beta:worker poll --on-work` per work item.
# The poller passes ANTHROPIC_{WORK_ID,ENVIRONMENT_ID,SESSION_ID,ENVIRONMENT_KEY}
# in env and the raw work JSON on stdin. We hand them all to on-work.py, which
# calls invoke_agent_runtime to wake the per-session microVM.
set -euo pipefail
exec python3 "$(dirname "$0")/on-work.py"
