import json
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from conftest import TEST_USER_ID
from exceptions.exceptions import BadRequestError, ForbiddenError, NotFoundError


@patch("controller.kinetics_controller.validate_and_save_kinetic_version")
def test_save_kinetics_investigation(mock_save, client):
    mock_save.return_value = {"status": "ok", "kinetic_investigation_id": 1, "version_id": 1}

    response = client.post(
        "/kinetics/investigation/save",
        data=json.dumps({"kinetic_sample_id": 1, "results": [], "comparison": {}}),
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.CREATED
    data = json.loads(response.data)
    assert data["kinetic_investigation_id"] == 1
    assert data["version_id"] == 1
    mock_save.assert_called_once()
    called_json, called_user_id = mock_save.call_args[0]
    assert called_json["kinetic_sample_id"] == 1
    assert called_user_id == TEST_USER_ID


@patch("controller.kinetics_controller.validate_and_save_kinetic_version")
def test_save_kinetics_investigation_bad_request(mock_save, client):
    mock_save.side_effect = BadRequestError("comparison.heuristic is required to save a version.")

    response = client.post(
        "/kinetics/investigation/save",
        data=json.dumps({"kinetic_sample_id": 1, "results": [], "comparison": {}}),
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("controller.kinetics_controller.get_kinetic_version")
def test_get_kinetics_version_success(mock_get_version, client):
    mock_get_version.return_value = {
        "version_id": 1, "kinetic_investigation_id": 1, "fitted_models": [], "comparison": {}
    }

    response = client.get("/kinetics/investigation/1/version/1")

    assert response.status_code == HTTPStatus.OK
    mock_get_version.assert_called_once_with(1, 1)


@patch("controller.kinetics_controller.get_kinetic_version")
def test_get_kinetics_version_not_found(mock_get_version, client):
    mock_get_version.side_effect = NotFoundError("Kinetic investigation 1 has no version 99.")

    response = client.get("/kinetics/investigation/1/version/99")

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("controller.kinetics_controller.get_kinetic_versions")
def test_get_kinetics_versions_list(mock_get_versions, client):
    mock_get_versions.return_value = [
        {"version_id": 1, "kinetic_investigation_id": 1, "fitted_models": [], "comparison": {}},
        {"version_id": 2, "kinetic_investigation_id": 1, "fitted_models": [], "comparison": {}},
    ]

    response = client.get("/kinetics/investigation/1/versions")

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert len(data["versions"]) == 2
    mock_get_versions.assert_called_once_with(1)


@patch("controller.kinetics_controller.get_kinetic_versions")
def test_get_kinetics_versions_not_found(mock_get_versions, client):
    mock_get_versions.side_effect = NotFoundError("Kinetic investigation 100 not found.")

    response = client.get("/kinetics/investigation/100/versions")

    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("controller.kinetics_controller.delete_kinetic_version")
def test_delete_kinetics_version(mock_delete_version, client):
    response = client.delete("/kinetics/investigation/1/version/1")

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data == {"kinetic_investigation_id": 1, "version_id": 1}
    mock_delete_version.assert_called_once_with(1, 1, TEST_USER_ID)


@patch("controller.kinetics_controller.delete_kinetic_version")
def test_delete_kinetics_version_forbidden(mock_delete_version, client):
    mock_delete_version.side_effect = ForbiddenError(
        "User is not authorized to delete this kinetic investigation version."
    )

    response = client.delete("/kinetics/investigation/1/version/1")

    assert response.status_code == HTTPStatus.FORBIDDEN


@patch("controller.kinetics_controller.get_all_kinetic_samples")
def test_should_pass_the_user_id_filter_to_the_samples_list(mock_list, client):
    """KLIST-H03"""
    mock_list.return_value = []

    response = client.get("/kinetics/samples?user_id=7")

    assert response.status_code == HTTPStatus.OK
    mock_list.assert_called_once_with(7)


@patch("controller.kinetics_controller.get_all_kinetic_samples")
def test_should_list_every_sample_when_no_user_id_is_sent(mock_list, client):
    """KLIST-H04"""
    mock_list.return_value = []

    client.get("/kinetics/samples")

    mock_list.assert_called_once_with(None)


@patch("controller.kinetics_controller.find_readable_kinetic_sample")
def test_should_answer_404_when_the_sample_is_not_readable(mock_find, client):
    """KDEL-N06: a deleted sample without versions is not found"""
    mock_find.side_effect = NotFoundError("Kinetic sample with id 5 doesn't exist.")

    response = client.get("/kinetics/sample/5")

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_find.assert_called_once_with(5)
