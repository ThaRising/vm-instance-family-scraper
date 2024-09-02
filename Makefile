SHELL := /bin/bash
.DEFAULT_GOAL := format

isort = poetry run isort
ruff = poetry run ruff --fix
black = poetry run black

.PHONY: format
format:
	$(black) .
	$(isort) -sl .
	$(ruff) .
	$(isort) -m 3 .
	$(black) .

.PHONY: test
test:
	@LOG_LEVEL=debug python -m unittest

.PHONY: mypy
mypy:
	@mypy --install-types
