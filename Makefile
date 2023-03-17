SEAFILE_VERSION = 7.1.3

build:
	docker build --progress=plain --tag seafile:${SEAFILE_VERSION} --build-arg SEAFILE_VERSION=${SEAFILE_VERSION} .
clear:
	docker compose down
	docker volume rm seafile
