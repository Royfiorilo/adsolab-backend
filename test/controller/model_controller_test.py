import json
from http import HTTPStatus
from unittest.mock import patch

from exceptions.exceptions import NotFoundError


@patch("controller.model_controller.find_models")
def test_get_models(mock_get_models, client, mock_models):
    mock_get_models.return_value = mock_models
    response = client.get("/models")

    data = json.loads(response.data)
    assert len(data["models"]) == 2
    assert response.status_code == HTTPStatus.OK
    mock_get_models.assert_called_once()


@patch("controller.model_controller.find_models")
def test_get_zero_models(mock_get_models, client):
    mock_get_models.side_effect = NotFoundError("No models found")
    response = client.get("/models")

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_get_models.assert_called_once()

@patch("controller.model_controller.find_models")
def test_get_models_server_error(mock_get_models, client):
    mock_get_models.side_effect = Exception("Database connection failed")
    response = client.get("/models")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_get_models.assert_called_once()

@patch("controller.model_controller.find_methods")
def test_get_methods_server_error(mock_find_methods, client):
    mock_find_methods.side_effect = Exception("Database connection failed")
    response = client.get("/models/methods")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_find_methods.assert_called_once()

@patch("controller.model_controller.find_methods")
def test_get_zero_methods(mock_get_methods, client):
    mock_get_methods.side_effect = NotFoundError("No adjust methods found")
    response = client.get("/models/methods")

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_get_methods.assert_called_once()

@patch("controller.model_controller.find_methods")
def test_get_methods(mock_get_methods, client, mock_methods):
    mock_get_methods.return_value = mock_methods
    response = client.get("/models/methods")

    data = json.loads(response.data)
    assert len(data["methods"]) == 2
    assert response.status_code == HTTPStatus.OK
    mock_get_methods.assert_called_once()