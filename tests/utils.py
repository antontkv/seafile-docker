import requests
from time import sleep

import docker
import pytest
from copy import deepcopy

class SeafileContainerSetup:
    def __init__(self) -> None:
        self._docker_client = docker.from_env()
        self._container_args = dict(
            image="seafile:7.1.3",
            name="test-seafile",
            detach=True,
            volumes={"test-seafile": {"bind": "/seafile/data", "mode": "rw"}},
            ports={8000: ("127.0.0.1", 8000), 8082: ("127.0.0.1", 8082), 8080: ("127.0.0.1", 8080)},
            environment={"ENABLE_WEBDAV": "True"}
        )
        self.volume = self._docker_client.volumes.create(name="test-seafile", driver="local")
        self.container = self._docker_client.containers.run(**self._container_args)

    def teardown(self) -> None:
        self.container.stop()
        self.container.remove()
        self.volume.remove()

    def restart(self) -> None:
        self.container.restart()

    def restart_with_disabled_seafdav(self) -> None:
        self.container.stop()
        self.container.remove()
        container_args = deepcopy(self._container_args)
        container_args["environment"]["ENABLE_WEBDAV"] = "False"
        self.container = self._docker_client.containers.run(**container_args)

    def restart_with_enabled_seafdav(self) -> None:
        self.container.stop()
        self.container.remove()
        self.container = self._docker_client.containers.run(**self._container_args)


@pytest.fixture(scope='session', autouse=True)
def seafile_container() -> SeafileContainerSetup:
    container_setup = SeafileContainerSetup()
    yield container_setup
    container_setup.teardown()

def wait_for_response_on_port(port: int, path: str = "/", timeout: int = 30) -> int:
    for _ in range(timeout):
        try:
            r = requests.get(f'http://localhost:{port}{path}', timeout=1)
            return r.status_code
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            sleep(1)
    raise TimeoutError
