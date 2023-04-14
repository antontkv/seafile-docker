import pytest

from .utils import SeafileAPI, SeafileContainerSetup, wait_for_response_on_port


@pytest.fixture(scope="session", autouse=True)
def seafile_container() -> SeafileContainerSetup:
    container_setup = SeafileContainerSetup()
    wait_for_response_on_port(8080)  # Wait when WebDAV will start, since it starts last
    yield container_setup
    container_setup.teardown()


@pytest.fixture(scope="session")
def seafile_api() -> SeafileAPI:
    seafile_api = SeafileAPI()
    seafile_api.create_test_data()
    yield seafile_api
