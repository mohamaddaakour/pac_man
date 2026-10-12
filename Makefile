.PHONY: install run demo test debug clean lint lint-strict
PYTHON ?= python3
CONFIG ?= config.json

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m pacman.main $(CONFIG)

demo:
	$(PYTHON) -m tools.cli_demo $(CONFIG)

test:
	$(PYTHON) -m pytest -q tests

debug:
	$(PYTHON) -m pdb -m pacman.main $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
