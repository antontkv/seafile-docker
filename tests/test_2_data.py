from .utils import SeafileAPI, SeafileContainerSetup, wait_for_response_on_port


def test_data_creation(seafile_api: SeafileAPI) -> None:
    seafile_api.create_test_data()
    assert seafile_api.get_test_file_contents() == "Hello Seafile"


def test_data_persistence(seafile_container: SeafileContainerSetup, seafile_api: SeafileAPI) -> None:
    seafile_container.restart()
    assert wait_for_response_on_port(8000, "/accounts/login/") == 200
    assert seafile_api.get_test_file_contents() == "Hello Seafile"
