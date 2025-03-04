import json
from http import HTTPStatus
from unittest.mock import patch

from exceptions.exceptions import NotFoundError, BadRequestError


@patch("controller.sample_controller.create_sample_db")
def test_create_sample_without_mandatory_param(mock_create_sample, client):
    mock_create_sample.side_effect = BadRequestError(f"Validation Error: ")

    response = client.post(
        "/sample",
        data=json.dumps({"title": "Test Sample",
                         "qe": [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768,
                                0.161924],
                         "adsorbate_id": 1,
                         "adsorbent_id": 3,
                         "temperature": 285,
                         "measure_unit": "mmol"
                         }),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    mock_create_sample.assert_called_once()


@patch("controller.sample_controller.create_sample_db")
def test_create_sample_without_optional_parameters(mock_create_sample, client, mock_sample):
    mock_create_sample.return_value = mock_sample.__dict__

    response = client.post(
        "/sample",
        data=json.dumps({"ce": [0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855],
                         "qe": [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768,
                                0.161924],
                         "adsorbate_id": 1,
                         "adsorbent_id": 3
                         }),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.CREATED

    mock_create_sample.assert_called_once()

@patch("controller.sample_controller.find_sample")
def test_get_sample_by_inexistent_sample_id(mock_find_sample, client):
    mock_find_sample.side_effect = NotFoundError(f"Sample with id 45 doesn't exist")
    response = client.get("/sample/45")

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_find_sample.assert_called_once()


@patch("controller.sample_controller.find_sample")
def test_get_sample_by_id(mock_find_sample, client, mock_sample):
    mock_find_sample.return_value = mock_sample.__dict__
    sample_id = 1
    response = client.get(f"/sample/{sample_id}")


    assert response.status_code == HTTPStatus.OK
    mock_find_sample.assert_called_once()
    data = json.loads(response.data)
    assert data["sample_id"] == sample_id
    assert len(data["ce"]) == len(data["qe"])


@patch("controller.sample_controller.find_sample")
def test_get_sample_server_error(mock_find_sample, client):
    mock_find_sample.side_effect = Exception("Database connection failed")
    sample_id = 1
    response = client.get(f"/sample/{sample_id}")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_find_sample.assert_called_once()

@patch('controller.sample_controller.create_sample_db')
def test_create_sample_server_error(mock_create_sample, client):
    mock_create_sample.side_effect = Exception("Database connection failed")

    response = client.post(
        "/sample",
        data=json.dumps(
            {"ce": [0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855],
             "qe": [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768,
                    0.161924],
             "adsorbate_id": 1,
             "adsorbent_id": 3
             }),
        content_type="application/json"
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_create_sample.assert_called_once()

@patch("controller.sample_controller.get_all_samples")
def test_get_all_samples(mock_get_all_samples, client, mock_samples):
    mock_get_all_samples.return_value = [sample.__dict__ for sample in mock_samples]
    response = client.get("/samples")

    data = json.loads(response.data)
    assert len(data["samples"]) == 2
    assert response.status_code == HTTPStatus.OK
    mock_get_all_samples.assert_called_once()


@patch("controller.sample_controller.get_all_samples")
def test_get_zero_samples(mock_get_all_samples, client):
    mock_get_all_samples.side_effect = NotFoundError("No samples found")
    response = client.get("/samples")

    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_get_all_samples.assert_called_once()

@patch("controller.sample_controller.get_all_samples")
def test_get_samples_server_error(mock_get_all_samples, client):
    mock_get_all_samples.side_effect = Exception("Database connection failed")
    response = client.get(f"/samples")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_get_all_samples.assert_called_once()


@patch("controller.sample_controller.delete_sample")
def test_delete_sample_server_error(mock_delete_sample, client):
    sample_id = 1
    mock_delete_sample.side_effect = Exception("Database connection failed")
    response = client.delete("/sample", content_type="application/json", data=json.dumps({'sample_id': sample_id}))
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_delete_sample.assert_called_once_with(sample_id)

@patch("controller.sample_controller.delete_sample")
def test_delete_sample(mock_delete_sample, client):
    sample_id = 1
    response = client.delete("/sample", content_type="application/json", data=json.dumps({'sample_id': sample_id}))
    assert response.status_code == HTTPStatus.OK
    mock_delete_sample.assert_called_once_with(sample_id)
    data = json.loads(response.data)
    assert data["sample_id"] == sample_id

@patch("controller.sample_controller.delete_sample")
def test_delete_sample_bad_request(mock_delete_sample, client):
    sample_id = 1
    response = client.delete("/sample", content_type="application/json", data=json.dumps({'sample': sample_id}))
    assert response.status_code == HTTPStatus.BAD_REQUEST
    mock_delete_sample.assert_not_called()

@patch("controller.sample_controller.delete_sample")
def test_delete_sample_doesnt_exist(mock_delete_sample, client):
    sample_id = 1
    mock_delete_sample.side_effect = NotFoundError(f"Sample with id {sample_id} doesn't exist")
    response = client.delete("/sample", content_type="application/json", data=json.dumps({'sample_id': sample_id}))
    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_delete_sample.assert_called_once_with(sample_id)


