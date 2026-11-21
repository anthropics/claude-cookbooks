"""The hard gates the Claude Cookbook's CI applies to a notebook, checked here first.

Mirrors tests/notebook_tests/test_notebooks.py in anthropics/claude-cookbooks: a notebook
is committed after a fresh-kernel "Run All", with outputs, no errors, no keys, and only
current model IDs.
"""

import re
from pathlib import Path

import nbformat
import pytest

NOTEBOOK = Path(__file__).resolve().parent.parent / "guide.ipynb"
CURRENT_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-haiku-5-5"}


@pytest.fixture(scope="module")
def notebook() -> nbformat.NotebookNode:
    return nbformat.read(NOTEBOOK, as_version=4)


@pytest.fixture(scope="module")
def code_cells(notebook: nbformat.NotebookNode) -> list:
    return [cell for cell in notebook.cells if cell.cell_type == "code"]


def test_is_a_valid_python_notebook(notebook: nbformat.NotebookNode) -> None:
    nbformat.validate(notebook)
    assert notebook.nbformat == 4
    assert notebook.metadata.kernelspec.language == "python"


def test_opens_with_a_title(notebook: nbformat.NotebookNode) -> None:
    first = notebook.cells[0]
    assert first.cell_type == "markdown" and first.source.startswith("# ")


def test_every_code_cell_ran_in_order_from_a_fresh_kernel(code_cells: list) -> None:
    assert [cell.execution_count for cell in code_cells] == list(range(1, len(code_cells) + 1))


def test_no_cell_is_empty(notebook: nbformat.NotebookNode) -> None:
    assert all(cell.source.strip() for cell in notebook.cells)


def test_no_error_outputs(code_cells: list) -> None:
    errors = [o for cell in code_cells for o in cell.outputs if o.output_type == "error"]
    assert not errors


def test_dependencies_are_installed_near_the_top(code_cells: list) -> None:
    installs = [i for i, cell in enumerate(code_cells) if "%pip install" in cell.source]
    assert installs and max(installs) < 3


def test_no_api_keys_anywhere() -> None:
    assert not re.search(r"sk-ant-[A-Za-z0-9_-]{8,}", NOTEBOOK.read_text())


def test_no_local_paths_in_outputs() -> None:
    assert "/Users/" not in NOTEBOOK.read_text()


def test_only_current_model_ids(code_cells: list) -> None:
    named = {m for cell in code_cells for m in re.findall(r"claude-[a-z0-9.-]+", cell.source)}
    assert named and named <= CURRENT_MODELS, named
