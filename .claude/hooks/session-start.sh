#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Install all dependencies including dev extras (playwright included)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Install Chromium via system Playwright (avoids CDN download restrictions)
# Python playwright will use the executable_path detected at runtime
playwright install chromium
