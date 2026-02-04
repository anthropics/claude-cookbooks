.PHONY: help format lint check fix test clean install sort-authors \
        test-notebooks test-notebooks-exec test-notebooks-tox test-notebooks-quick

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "  Code Quality:"
	@echo "    make format              - Format code with ruff"
	@echo "    make lint                - Run ruff linting checks"
	@echo "    make check               - Run all checks (format check + lint)"
	@echo "    make fix                 - Auto-fix issues with ruff"
	@echo ""
	@echo "  Testing:"
	@echo "    make test                - Run all pytest tests"
	@echo "    make test-notebooks      - Run notebook structure tests (fast)"
	@echo "    make test-notebooks-exec - Run notebook execution tests (slow, needs API key)"
	@echo "    make test-notebooks-tox  - Run notebook tests in isolated tox environment"
	@echo "    make test-notebooks-quick- Quick validation of all notebooks"
	@echo ""
	@echo "  Setup:"
	@echo "    make install             - Install dependencies"
	@echo "    make clean               - Remove cache files"
	@echo "    make sort-authors        - Sort authors.yaml alphabetically"
	@echo ""
	@echo "  Notebook test options (via environment variables):"
	@echo "    NOTEBOOK=path/to/notebook.ipynb  - Test specific notebook"
	@echo "    NOTEBOOK_DIR=capabilities        - Test notebooks in directory"
	@echo ""
	@echo "  Examples:"
	@echo "    make test-notebooks NOTEBOOK=tool_use/calculator_tool.ipynb"
	@echo "    make test-notebooks-tox NOTEBOOK_DIR=capabilities"

# Format code with ruff
format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

# Check if code is formatted without changing it
format-check:
	@echo "Checking code formatting with ruff..."
	uv run ruff format --check .

# Run ruff linting
lint:
	@echo "Running ruff linting..."
	uv run ruff check .

# Run all checks
check: format-check lint
	@echo "All checks completed!"

# Auto-fix issues with ruff
fix:
	@echo "Auto-fixing issues with ruff..."
	uv run ruff check --fix .
	uv run ruff format .

# Run tests
test:
	@echo "Running tests..."
	uv run pytest

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync --all-extras

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cache cleaned!"

# Sort authors.yaml alphabetically
sort-authors:
	@echo "Sorting authors.yaml..."
	uv run python scripts/validate_authors_sorted.py --fix

# Notebook testing targets
# ========================

# Run notebook structure tests (fast, no API calls)
test-notebooks:
	@echo "Running notebook structure tests..."
ifdef NOTEBOOK
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=short -rf --notebook $(NOTEBOOK)
else ifdef NOTEBOOK_DIR
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=short -rf --notebook-dir $(NOTEBOOK_DIR)
else
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=short -rf -m "not slow"
endif

# Run notebook execution tests (slow, requires API key)
test-notebooks-exec:
	@echo "Running notebook execution tests (this may take a while)..."
ifdef NOTEBOOK
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=long --execute-notebooks --notebook $(NOTEBOOK)
else ifdef NOTEBOOK_DIR
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=long --execute-notebooks --notebook-dir $(NOTEBOOK_DIR)
else
	uv run pytest tests/notebook_tests/test_notebooks.py -v --tb=long --execute-notebooks
endif

# Run notebook tests in isolated tox environment
test-notebooks-tox:
	@echo "Running notebook tests in tox environment..."
ifdef NOTEBOOK
	uv run tox -e structure-single -- $(NOTEBOOK)
else ifdef NOTEBOOK_DIR
	uv run tox -e structure -- --notebook-dir $(NOTEBOOK_DIR)
else
	uv run tox -e structure
endif

# Quick validation of all notebooks without pytest
test-notebooks-quick:
	@echo "Running quick notebook validation..."
ifdef NOTEBOOK
	uv run python scripts/test_notebooks.py --quick --notebook $(NOTEBOOK)
else ifdef NOTEBOOK_DIR
	uv run python scripts/test_notebooks.py --quick --dir $(NOTEBOOK_DIR)
else
	uv run python scripts/test_notebooks.py --list
endif
