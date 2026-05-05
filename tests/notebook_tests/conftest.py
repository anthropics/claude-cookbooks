"""Pytest hooks for notebook-specific test reporting."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.reports import TestReport
    from _pytest.terminal import TerminalReporter


# Store failures grouped by notebook
_notebook_failures: dict[str, set[str]] = defaultdict(set)

# Human-readable names for test categories
_ISSUE_NAMES = {
    "all_cells_executed": "unexecuted cells",
    "cells_executed_in_order": "out-of-order execution",
    "execution_counts_start_from_one": "stale kernel",
    "no_error_outputs": "error outputs",
    "no_hardcoded_api_keys": "hardcoded API key",
    "api_key_from_environment": "API key not from env",
    "python_kernel": "non-Python kernel",
    "valid_json": "invalid JSON",
    "has_cells": "no cells",
    "has_code_cells": "no code cells",
    "no_deprecated_models": "deprecated model",
}


def _extract_notebook_path(nodeid: str) -> str | None:
    """Extract notebook path from test node ID."""
    match = re.search(r"\[([^\]]+\.ipynb)\]", nodeid)
    return match.group(1) if match else None


def _extract_test_name(nodeid: str) -> str:
    """Extract test function name from test node ID."""
    match = re.search(r"::test_(\w+)\[", nodeid)
    return match.group(1) if match else "unknown"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    """Collect failures grouped by notebook."""
    outcome = yield
    report: TestReport = outcome.get_result()

    if report.when == "call" and report.failed:
        notebook = _extract_notebook_path(item.nodeid)
        if notebook:
            test_name = _extract_test_name(item.nodeid)
            issue = _ISSUE_NAMES.get(test_name, test_name.replace("_", " "))
            _notebook_failures[notebook].add(issue)


def pytest_terminal_summary(
    terminalreporter: TerminalReporter, exitstatus: int, config: Config
) -> None:
    """Print a summary of failures grouped by notebook."""
    if not _notebook_failures:
        return

    tr = terminalreporter
    tr.write_sep("=", "NOTEBOOK FAILURE SUMMARY", bold=True, yellow=True)
    tr.write("\n")

    # Count totals
    total_notebooks = len(_notebook_failures)
    total_issues = sum(len(issues) for issues in _notebook_failures.values())

    tr.write(
        f"Found issues in {total_notebooks} notebook(s) ({total_issues} total issue types)\n\n"
    )

    # Group by issue type for a quick overview
    issue_counts: dict[str, list[str]] = defaultdict(list)
    for notebook, issues in _notebook_failures.items():
        for issue in issues:
            issue_counts[issue].append(notebook)

    tr.write("Issue breakdown:\n", bold=True)
    for issue, notebooks in sorted(issue_counts.items(), key=lambda x: -len(x[1])):
        tr.write(f"  {issue}: {len(notebooks)} notebook(s)\n")
    tr.write("\n")

    # Group notebooks by directory for cleaner output
    by_directory: dict[str, list[tuple[str, set[str]]]] = defaultdict(list)
    for notebook in sorted(_notebook_failures.keys()):
        parts = notebook.split("/")
        if len(parts) > 1:
            directory = parts[0]
            filename = "/".join(parts[1:])
        else:
            directory = "."
            filename = notebook
        by_directory[directory].append((filename, _notebook_failures[notebook]))

    tr.write("By notebook:\n", bold=True)
    for directory in sorted(by_directory.keys()):
        tr.write(f"\n  {directory}/\n", bold=True)
        for filename, issues in by_directory[directory]:
            issue_list = ", ".join(sorted(issues))
            tr.write(f"    {filename}\n")
            tr.write(f"      -> {issue_list}\n", red=True)

    tr.write("\n")
    _notebook_failures.clear()


def pytest_configure(config: Config) -> None:
    """Reset failure tracking at start of test run."""
    _notebook_failures.clear()
