SEAFILE_VERSION = 8.0.3

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

.PHONY: update.requirements
update.requirements: ## Update requirements
	@.venv/bin/pip-compile --resolver=backtracking -U requirements-dev.in
	@.venv/bin/pip-sync requirements-dev.txt

.PHONY: update.precommit
update.precommit: ## Update pre-commit repos
	@.venv/bin/pre-commit autoupdate

.PHONY: lint
lint: ## Launch black and ruff
	-@.venv/bin/black -l120 .
	-@.venv/bin/ruff check --fix --show-fixes --exit-non-zero-on-fix . && echo "Ruff OK"

.PHONY: build
build: ## Build docker container
	docker build --progress=plain --tag ghcr.io/antontkv/seafile:${SEAFILE_VERSION} --build-arg SEAFILE_VERSION=${SEAFILE_VERSION} .

.PHONY: test
test: ## Run tests
	@.venv/bin/python -m pytest

.PHONY: test.last_failed
test.last_failed: ## Run last failed tests
	@.venv/bin/python -m pytest --lf

.PHONY: up
up: ## Start the container
	@docker compose up -d

.PHONY: down
down: ## Stop the container
	@docker compose down

.PHONY: down.clean
down.clean: down ## Stop the container and remove data volume
	@docker compose down -v

.PHONY: logs
logs: ## Show container logs
	@docker compose logs

.PHONY: status
status: ## Show container and volume status
	@scripts/status

.PHONY: backup
backup: ## Create a backup archive
	@docker exec -it seafile backup start
	sudo tar -czvf backup.tar -C /var/lib/docker/volumes/seafile/_data .
	@docker exec -it seafile backup end

.PHONY: restore
restore: down.clean ## Restore a backup archive
	@docker compose create
	sudo tar --same-owner -xvf backup.tar -C /var/lib/docker/volumes/seafile/_data
	@docker compose up -d
