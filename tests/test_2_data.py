from .utils import SeafileAPI, SeafileContainerSetup, get_test_file_contents_via_webdav, wait_for_response_on_port


def test_data_creation(seafile_api: SeafileAPI) -> None:
    assert seafile_api.get_test_file_contents() == "Hello Seafile"


def test_data_persistence(seafile_container: SeafileContainerSetup, seafile_api: SeafileAPI) -> None:
    seafile_container.restart()
    assert wait_for_response_on_port(8000, "/accounts/login/") == 200
    assert seafile_api.get_test_file_contents() == "Hello Seafile"


def test_seafdav(seafile_api: SeafileAPI):
    assert wait_for_response_on_port(8080) == 401
    assert get_test_file_contents_via_webdav() == "Hello Seafile"
