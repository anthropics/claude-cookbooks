#!/bin/bash
# PreToolUse Hook - Write Safety Check
# Prevents accidental overwrites of key files

set -e

TOOL_NAME="$1"
FILE_PATH="$2"

# Only run for Write tool
if [[ "$TOOL_NAME" != "Write" ]]; then
    exit 0
fi

# Protected files - should never be overwritten without explicit user request
PROTECTED_FILES=(
    ".env"
    "requirements.txt"
)

for protected in "${PROTECTED_FILES[@]}"; do
    if [[ "$FILE_PATH" == *"$protected"* ]]; then
        echo "⚠️  WARNING: Attempting to write to protected file: $FILE_PATH"
        echo "This file should rarely be modified. Proceeding with caution..."
        # Allow but warn - don't block
    fi
done

# Warn if writing to notebooks/ without .ipynb extension
if [[ "$FILE_PATH" == *"notebooks/"* ]] && [[ "$FILE_PATH" != *".ipynb" ]]; then
    echo "⚠️  Writing non-notebook file to notebooks/ directory: $FILE_PATH"
fi

# Warn if writing to sample_data/
if [[ "$FILE_PATH" == *"sample_data/"* ]]; then
    echo "ℹ️  Modifying sample data: $FILE_PATH"
fi

exit 0
