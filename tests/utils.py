from copy import deepcopy
from time import sleep

import docker
import requests


class SeafileContainerSetup:
    def __init__(self) -> None:
        self._docker_client = docker.from_env()
        self._container_args = dict(
            image="ghcr.io/antontkv/seafile:9.0.10",
            name="test-seafile",
            detach=True,
            volumes={"test-seafile": {"bind": "/seafile/data", "mode": "rw"}},
            ports={8000: ("127.0.0.1", 8000), 8082: ("127.0.0.1", 8082), 8080: ("127.0.0.1", 8080)},
            environment={"ENABLE_WEBDAV": "True"},
        )

        # Removing left over container, if they left after previous runs
        try:
            self._docker_client.containers.get("test-seafile").stop()
            self._docker_client.containers.get("test-seafile").remove()
            self._docker_client.volumes.get("test-seafile").remove()
        except docker.errors.NotFound:
            pass

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


class SeafileAPI:
    def __init__(self) -> None:
        self.base_url = "http://localhost:8000/api2"
        self.session = requests.Session()
        self._login()

    def _login(self) -> None:
        token_request = self.session.post(
            f"{self.base_url}/auth-token/", data={"username": "me@example.com", "password": "asecret"}, timeout=5
        )
        if token_request.status_code != 200:
            raise ConnectionError(f"Can't login. Seafile returned {token_request.status_code} status")
        self.token = token_request.json()["token"]
        self.session.headers["Authorization"] = f"Token {self.token}"
        token_check = self.session.get(f"{self.base_url}/auth/ping/", timeout=5)
        if token_check.json() != "pong":
            raise ConnectionError("Can't authorize with provided token")

    def create_test_library(self) -> str:
        lib_request = self.session.post(f"{self.base_url}/repos/", data={"name": "test_lib"}, timeout=5)
        if lib_request.status_code != 200:
            raise ConnectionError(f"Can't create test_lib library. Seafile returned {lib_request.status_code} status")
        self.test_lib_id = lib_request.json()["repo_id"]
        return self.test_lib_id

    def get_test_library_id(self) -> str:
        lib_request = self.session.get(f"{self.base_url}/repos/?nameContains=test_lib", timeout=5)
        if not lib_request.json():
            raise ValueError("Seafile test_lib library doesn't exist")
        self.test_lib_id = lib_request.json()[0]["id"]
        return self.test_lib_id

    def create_test_file(self) -> None:
        upload_link_r = self.session.get(f"{self.base_url}/repos/{self.test_lib_id}/upload-link/", timeout=5)
        if upload_link_r.status_code != 200:
            raise ConnectionError(f"Can't get upload link. Seafile returned {upload_link_r.status_code} status")
        upload_url = upload_link_r.json()
        upload_file_r = self.session.post(
            upload_url, files={"file": ("hello.txt", "Hello Seafile"), "parent_dir": "/", "repalce": 1}, timeout=5
        )
        if upload_file_r.status_code != 200:
            raise ConnectionError(f"Can't create test file. Seafile returned {upload_file_r.status_code} status")

    def get_test_file_contents(self) -> str:
        self.get_test_library_id()
        download_link_r = self.session.get(f"{self.base_url}/repos/{self.test_lib_id}/file/?p=/hello.txt", timeout=5)
        if download_link_r.status_code != 200:
            raise ConnectionError(f"Can't get download link. Seafile returned {download_link_r.status_code} status")
        download_url = download_link_r.json()
        download_file = self.session.get(download_url, timeout=5)
        return download_file.text

    def create_test_data(self) -> None:
        self.create_test_library()
        self.create_test_file()


def get_test_file_contents_via_webdav() -> str:
    return requests.get(
        "http://localhost:8080/seafdav/test_lib/hello.txt", auth=("me@example.com", "asecret"), timeout=5
    ).text


def wait_for_response_on_port(port: int, path: str = "/", timeout: int = 30) -> int:
    for _ in range(timeout):
        try:
            r = requests.get(f"http://localhost:{port}{path}", timeout=1)
            return r.status_code
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            sleep(1)
    raise TimeoutError
