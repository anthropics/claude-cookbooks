#!/usr/bin/env bash
# Two modes:
#   (default)  Ephemeral: run the agent once on $PROMPT, print the result, exit.
#   serve      Start the FastAPI server on :8000.
set -euo pipefail

if [[ "${1:-}" == "serve" ]]; then
  exec uvicorn hosting.server:app --host 0.0.0.0 --port 8000
fi

# Ephemeral: run the research agent from notebook 00 once on $PROMPT and exit.
exec python -m hosting.run_once
