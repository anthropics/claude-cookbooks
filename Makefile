.PHONY: help format lint check fix test clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  make format        - Format code with ruff"
	@echo "  make lint          - Run ruff linting checks"
	@echo "  make check         - Run all checks (format check + lint)"
	@echo "  make fix           - Auto-fix issues with ruff"
	@echo "  make test          - Run tests"
	@echo "  make install       - Install dependencies"
	@echo "  make clean         - Remove cache files"

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
