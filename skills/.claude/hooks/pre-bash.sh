#!/bin/bash
# PreToolUse Hook - Bash Safety Check
# Prevents dangerous commands and provides helpful reminders

set -e

TOOL_NAME="$1"
COMMAND="$2"

# Only run for Bash tool
if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

# Check for potentially dangerous commands
if [[ "$COMMAND" == *"rm -rf outputs"* ]] || [[ "$COMMAND" == *"rm -rf sample_data"* ]]; then
    echo "⚠️  WARNING: Attempting to delete important directory!"
    echo "Command: $COMMAND"
    echo "These directories contain generated files and sample data."
    # Allow but warn
fi

# Warn about pip install without using requirements.txt
if [[ "$COMMAND" == *"pip install"* ]] && [[ "$COMMAND" != *"requirements.txt"* ]]; then
    echo "ℹ️  Installing package directly. Consider updating requirements.txt"
fi

# Remind about kernel restart after SDK reinstall
if [[ "$COMMAND" == *"pip install"* ]] && [[ "$COMMAND" == *"anthropic"* ]]; then
    echo "ℹ️  Remember: Restart Jupyter kernel after SDK installation!"
fi

# Warn if trying to start jupyter/servers
if [[ "$COMMAND" == *"jupyter notebook"* ]] || [[ "$COMMAND" == *"jupyter lab"* ]]; then
    echo "ℹ️  Starting Jupyter. Make sure to select the venv kernel in notebooks."
fi

exit 0
