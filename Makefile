.PHONY: help setup verify test lint clean

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

help:
	@echo "Targets:"
	@echo "  setup   - create a venv and install dev dependencies"
	@echo "  verify  - run scripts/verify_setup.sh"
	@echo "  test    - run pytest"
	@echo "  lint    - run ruff"
	@echo "  clean   - remove venv and caches"

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

verify:
	bash scripts/verify_setup.sh

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check .

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache **/__pycache__ *.egg-info
