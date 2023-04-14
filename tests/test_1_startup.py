import pytest

from .utils import SeafileContainerSetup, wait_for_response_on_port


def test_cold_startup_seafile() -> None:
    assert wait_for_response_on_port(8082) == 404


def test_cold_startup_seahub() -> None:
    assert wait_for_response_on_port(8000, "/accounts/login/") == 200


def test_cold_startup_seafdav() -> None:
    assert wait_for_response_on_port(8080) == 401


def test_with_disabled_seafdav(seafile_container: SeafileContainerSetup) -> None:
    seafile_container.restart_with_disabled_seafdav()
    with pytest.raises(TimeoutError):
        wait_for_response_on_port(8080)


def test_with_reenabled_seafdav(seafile_container: SeafileContainerSetup) -> None:
    seafile_container.restart_with_enabled_seafdav()
    assert wait_for_response_on_port(8080) == 401
