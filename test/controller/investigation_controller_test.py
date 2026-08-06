import json
from http import HTTPStatus
from unittest.mock import patch, MagicMock

from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from conftest import TEST_USER_ID
from exceptions.exceptions import NotFoundError, BadRequestError


@patch("controller.investigation_controller.run_linearization_models")
def test_execute_linear_models(mock_run_models, client, valid_linear_model_data):
    sample_id = 1
    models = [
        {
            "model": 1,
            "linearizations": [
                "1", "2"
            ]
        },
        {
            "model": 2,
            "linearizations": [
                "3"
            ]
        },
        {
            "model": 2,
            "linearizations": [
                "3"
            ]
        }
    ]
    mock_run_models.return_value = valid_linear_model_data

    response = client.post(
        "/investigation/run-linearization",
        data=json.dumps({"sample_id": sample_id, "models": models}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.OK
    mock_run_models.assert_called_once()
    data = json.loads(response.data)
    assert data["sample_id"] == sample_id
    assert len(data["results"]) == 2


@patch("controller.investigation_controller.run_linearization_models")
def test_execute_linear_models_missing_params(mock_run_models, client):
    response = client.post(
        "/investigation/run-linearization",
        data=json.dumps({"investigation_id": 1}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    mock_run_models.assert_not_called()


@patch("controller.investigation_controller.run_no_linear_models")
def test_execute_no_linear_models(mock_run_models, client, valid_comparison_data, valid_fitted_model_data):
    sample_id = 1
    iteration = 10000
    models = [
        {
            "model": 1,
            "seeds": [
                {"name": "k", "value": 96.7092, "stderr": 0.0002},
                {"name": "qmax", "value": 0.0318, "stderr": 1949.9258}
            ]
        },
        {
            "model": 2,
            "seeds": [
                {"name": "kf", "value": 0.1291, "stderr": 2.4419},
                {"name": "nf", "value": 2.0885, "stderr": 0.0176}
            ]
        }
    ]

    mock_run_models.return_value = ([valid_fitted_model_data], valid_comparison_data)

    response = client.post(
        "/investigation/run-no-linear-model",
        data=json.dumps({"sample_id": sample_id, "iteration": iteration, "models": models}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.OK
    mock_run_models.assert_called_once()
    data = json.loads(response.data)
    assert data["sample_id"] == sample_id
    assert data["results"] == [valid_fitted_model_data]
    assert data["comparison"] == valid_comparison_data


@patch("controller.investigation_controller.run_no_linear_models")
def test_execute_no_linear_models_missing_params(mock_run_models, client):
    response = client.post(
        "/investigation/run-no-linear-model",
        data=json.dumps({"models": ["model1"]}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    mock_run_models.assert_not_called()


@patch("controller.investigation_controller.get_investigations_from_db")
def test_get_investigations(mock_get_investigations, client):
    mock_investigation1 = MagicMock()
    mock_investigation2 = MagicMock()
    mock_get_investigations.return_value = {"investigations": [mock_investigation1, mock_investigation2],
                                            "page": 1, "per_page": 20, "total": 2, "pages": 1}

    with patch.object(INVESTIGATION_SCHEMA, 'dump', side_effect=lambda x: {"investigation_id": 1}):
        response = client.get("/investigations")

        assert response.status_code == HTTPStatus.OK
        mock_get_investigations.assert_called_once()
        data = json.loads(response.data)
        assert "investigations" in data
        assert len(data["investigations"]) == 2


@patch("controller.investigation_controller.validate_and_save_version")
def test_save_version(mock_save_version, client, mock_version, valid_comparison_data, valid_fitted_model_data):
    mock_save_version.return_value = mock_version
    sample_id = 1

    response = client.post(
        "/investigation/save",
        data=json.dumps({"sample_id": sample_id, "investigation_id": 1, "results": [valid_fitted_model_data],
                         "comparison": valid_comparison_data}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.CREATED
    mock_save_version.assert_called_once()
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["version_id"] == mock_version.version_id


@patch("controller.investigation_controller.validate_and_save_version")
def test_save_version_missing_sample_id(mock_save_version, client):
    response = client.post(
        "/investigation/save",
        data=json.dumps({"results": []}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    mock_save_version.assert_not_called()


@patch("controller.investigation_controller.validate_and_save_version")
def test_save_version_exception(mock_save_version, client):
    mock_save_version.side_effect = Exception("Test exception")

    response = client.post(
        "/investigation/save",
        data=json.dumps({"sample_id": 3}),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


@patch('controller.investigation_controller.get_version')
def test_get_investigation_version_success(mock_get_version, client, investigation_id, version_id, valid_version_data):
    mock_get_version.return_value = valid_version_data

    response = client.get(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == valid_version_data
    mock_get_version.assert_called_once_with(investigation_id, version_id)


@patch('controller.investigation_controller.get_version')
def test_get_investigation_version_not_found(mock_get_version, client, investigation_id):
    version_id = 200
    mock_get_version.side_effect = NotFoundError(f"Investigation with ID {investigation_id} don't have version {version_id}")

    response = client.get(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_get_version.assert_called_once_with(investigation_id, version_id)


@patch('controller.investigation_controller.get_version')
def test_get_investigation_version_server_error(mock_get_version, client, investigation_id, version_id):
    mock_get_version.side_effect = Exception("Database connection failed")

    response = client.get(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_get_version.assert_called_once_with(investigation_id, version_id)


@patch('controller.investigation_controller.get_versions_by_investigation')
def test_get_investigation_versions_success(mock_get_versions_by_investigation, client, investigation_id, versions_list):
    mock_get_versions_by_investigation.return_value = versions_list

    response = client.get(f'/investigation/{investigation_id}/versions')

    assert response.status_code == HTTPStatus.OK
    result = json.loads(response.data)
    assert result["investigation_id"] == investigation_id
    assert result["versions"] == versions_list
    mock_get_versions_by_investigation.assert_called_once_with(investigation_id)


@patch('controller.investigation_controller.get_versions_by_investigation')
def test_get_investigation_versions_empty(mock_get_versions_by_investigation, client, investigation_id):
    mock_get_versions_by_investigation.return_value = []

    response = client.get(f'/investigation/{investigation_id}/versions')

    assert response.status_code == HTTPStatus.OK
    result = json.loads(response.data)
    assert result["investigation_id"] == investigation_id
    assert result["versions"] == []
    mock_get_versions_by_investigation.assert_called_once_with(investigation_id)


@patch('controller.investigation_controller.get_versions_by_investigation')
def test_get_investigation_versions_not_found(mock_get_versions_by_investigation, client):
    investigation_id = 100
    mock_get_versions_by_investigation.side_effect = NotFoundError(f"Investigation with ID {investigation_id} not found")

    response = client.get(f'/investigation/{investigation_id}/versions')

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_get_versions_by_investigation.assert_called_once_with(investigation_id)

@patch('controller.investigation_controller.delete_investigation')
def test_delete_investigation_server_error(mock_delete_investigation, client, investigation_id):
    mock_delete_investigation.side_effect = Exception("Database connection failed")

    response = client.delete(f'/investigation/{investigation_id}')

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_delete_investigation.assert_called_once_with(investigation_id, TEST_USER_ID)


@patch('controller.investigation_controller.delete_investigation')
def test_delete_investigation_not_exist(mock_delete_investigation, client):
    investigation_id = 200
    mock_delete_investigation.side_effect = NotFoundError(f"Investigation with ID {investigation_id} not found")

    response = client.delete(f'/investigation/{investigation_id}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_delete_investigation.assert_called_once_with(investigation_id, TEST_USER_ID)

@patch('controller.investigation_controller.delete_investigation')
def test_delete_investigation(mock_delete_investigation, client, investigation_id):
    mock_delete_investigation.return_value = {"investigation_id": investigation_id}

    response = client.delete(f'/investigation/{investigation_id}')
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data['investigation_id'] == investigation_id
    mock_delete_investigation.assert_called_once_with(investigation_id, TEST_USER_ID)

@patch('controller.investigation_controller.is_valid_investigation')
@patch('controller.investigation_controller.delete_investigation_version')
def test_delete_version(mock_delete_version, mock_is_valid_investigation, client, investigation_id, version_id):
    mock_delete_version.return_value = {"investigation_id": investigation_id, "version_id": version_id}

    response = client.delete(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data['investigation_id'] == investigation_id
    assert data['version_id'] == version_id
    mock_delete_version.assert_called_once_with(investigation_id, version_id)

@patch('controller.investigation_controller.is_valid_investigation')
@patch('controller.investigation_controller.delete_investigation_version')
def test_delete_version_server_error(mock_delete_version, mock_is_valid_investigation, client, investigation_id,version_id):
    mock_delete_version.side_effect = Exception("Database connection failed")

    response = client.delete(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_delete_version.assert_called_once_with(investigation_id, version_id)


@patch('controller.investigation_controller.is_valid_investigation')
@patch('controller.investigation_controller.delete_investigation_version')
def test_delete_version_of_investigation_not_exist(mock_delete_version, mock_is_valid_investigation, client,version_id):
    investigation_id = 200
    mock_delete_version.side_effect = NotFoundError(f"Investigation with ID {investigation_id} not found")

    response = client.delete(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_delete_version.assert_called_once_with(investigation_id, version_id)

@patch('controller.investigation_controller.is_valid_investigation')
@patch('controller.investigation_controller.delete_investigation_version')
def test_delete_version_not_exist(mock_delete_version, mock_is_valid_investigation, client,investigation_id):
    version_id = 200
    mock_delete_version.side_effect = NotFoundError(f"Investigation with ID {investigation_id} don't have version {version_id}")

    response = client.delete(f'/investigation/{investigation_id}/version/{version_id}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_delete_version.assert_called_once_with(investigation_id, version_id)