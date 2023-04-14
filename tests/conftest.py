import pytest

from .utils import SeafileAPI, SeafileContainerSetup


@pytest.fixture(scope="session", autouse=True)
def seafile_container() -> SeafileContainerSetup:
    container_setup = SeafileContainerSetup()
    yield container_setup
    container_setup.teardown()


@pytest.fixture(scope="module")
def seafile_api() -> SeafileAPI:
    seafile_api = SeafileAPI()
    yield seafile_api
