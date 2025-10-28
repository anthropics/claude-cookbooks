#!/usr/bin/env python3
"""Validate notebook structure and content."""

import json
import sys
from pathlib import Path


def validate_notebook(path: Path) -> list:
    """Validate a single notebook."""
    issues = []

    with open(path) as f:
        nb = json.load(f)

    # Check for empty cells
    for i, cell in enumerate(nb["cells"]):
        if not cell.get("source"):
            issues.append(f"Cell {i}: Empty cell found")

    # Check for error outputs
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    issues.append(f"Cell {i}: Contains error output")

    return issues


def main():
    """Check notebooks passed as arguments."""
    has_issues = False

    # Get notebook paths from command line arguments
    notebooks = [Path(arg) for arg in sys.argv[1:] if arg.endswith(".ipynb")]

    if not notebooks:
        print("⚠️ No notebooks to validate")
        sys.exit(0)

    for notebook in notebooks:
        issues = validate_notebook(notebook)
        if issues:
            has_issues = True
            print(f"\n❌ {notebook}:")
            for issue in issues:
                print(f"  - {issue}")

    if not has_issues:
        print(f"✅ All {len(notebooks)} notebook(s) validated successfully")
    else:
        print("\n❌ Found issues that must be fixed before committing")

    # Exit with error if issues found in changed files
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
