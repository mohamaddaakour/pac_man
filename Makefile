.PHONY: install run demo test debug clean lint lint-strict
PYTHON ?= python3
CONFIG ?= config.json

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) pac-man.py $(CONFIG)

demo:
	$(PYTHON) tools/cli_demo.py $(CONFIG)

test:
	$(PYTHON) -m pytest ./tests/*

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict