import pytest

from .utils import SeafileContainerSetup


@pytest.fixture(scope="session", autouse=True)
def seafile_container() -> SeafileContainerSetup:
    container_setup = SeafileContainerSetup()
    yield container_setup
    container_setup.teardown()
