SEAFILE_VERSION = 7.1.3

.PHONY: help
help: ## Show help
	@egrep '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Setup environment
	@if ! python3 --version | grep -c "3\.11" > /dev/null; then \
		echo "$$(tput setaf 1)Use Python 3.11$$(tput sgr0)"; \
		exit; fi
	@if ! [ -d ".venv" ]; then python3 -m venv .venv; fi
	@. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install pip-tools && \
	pip install --upgrade pip-tools && \
	if ! [ -f requirements-dev.txt ]; then pip-compile --resolver=backtracking requirements-dev.in; fi && \
	pip-sync requirements-dev.txt && \
	pre-commit install && \
	pre-commit run --all-files

.PHONY: requirements
requirements: ## Resolve dependencies from .in files and update environment
	@.venv/bin/pip-compile --resolver=backtracking requirements-dev.in
	@.venv/bin/pip-sync requirements-dev.txt

.PHONY: lint
lint: ## Launch black and ruff
	-@.venv/bin/black -l120 .
	-@.venv/bin/ruff check --fix --show-fixes --exit-non-zero-on-fix . && echo "Ruff OK"

.PHONY: build
build: ## Build docker container
	docker build --progress=plain --tag seafile:${SEAFILE_VERSION} --build-arg SEAFILE_VERSION=${SEAFILE_VERSION} .

.PHONY: test
test: ## Run tests
	@.venv/bin/python -m pytest -x
