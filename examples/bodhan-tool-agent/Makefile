.PHONY: install check test lint fmt clean

install:
	python -m pip install -e ".[dev]"

check: lint test

lint:
	ruff check src tests

fmt:
	ruff format src tests

test:
	pytest -q

clean:
	rm -rf .pytest_cache .cache out **/__pycache__
