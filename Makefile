SEAFILE_VERSION = 7.1.3

build:
	docker build --tag seafile:${SEAFILE_VERSION} --build-arg SEAFILE_VERSION=${SEAFILE_VERSION} .
