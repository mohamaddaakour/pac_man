.PHONY: install run demo graphical-demo test debug clean lint lint-strict
# Use the project environment when available; allow PYTHON=... overrides.
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
CONFIG ?= config.json

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m pacman.main $(CONFIG)

demo:
	$(PYTHON) -m tools.cli_demo $(CONFIG)

graphical-demo:
	$(PYTHON) -m tools.graphical_demo $(CONFIG)

test:
	$(PYTHON) -m pytest -q tests

debug:
	$(PYTHON) -m pdb -m pacman.main $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
