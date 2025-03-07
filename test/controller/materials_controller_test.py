import json
from unittest.mock import patch

from exceptions.exceptions import BadRequestError


@patch('controller.materials_controller.dump_adsorbates')
@patch('controller.materials_controller.get_all_adsorbates')
def test_get_adsorbates(mock_get_all_adsorbates, mock_dump_adsorbates, client):
    adsorbate_data = [{'id': 1, 'ion_name': 'Carbon', 'iupac_name': 'C', 'formula': 'CO2'}]
    mock_get_all_adsorbates.return_value = adsorbate_data
    mock_dump_adsorbates.return_value = adsorbate_data

    response = client.get('/adsorbates')

    mock_get_all_adsorbates.assert_called_once_with()
    mock_dump_adsorbates.assert_called_once_with(adsorbate_data)

    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'adsorbates' in data
    assert len(data['adsorbates']) == len(adsorbate_data)

@patch('controller.materials_controller.dump_adsorbents')
@patch('controller.materials_controller.get_all_adsorbents')
def test_get_adsorbents(mock_get_all_adsorbents, mock_dump_adsorbents, client):
    adsorbent_data = [{'id': 1, 'name': 'Metal'}]
    mock_get_all_adsorbents.return_value = adsorbent_data
    mock_dump_adsorbents.return_value = adsorbent_data

    response = client.get('/adsorbents')

    mock_get_all_adsorbents.assert_called_once_with()
    mock_dump_adsorbents.assert_called_once_with(adsorbent_data)

    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'adsorbents' in data
    assert len(data['adsorbents']) == len(adsorbent_data)


@patch('controller.materials_controller.sync_materials')
def test_get_materials_sync_success(mock_sync_materials, client):
    response = client.get('/materials_sync')

    mock_sync_materials.assert_called_once_with()

    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['message'] == 'Materials syncronized'
    assert data['status'] == 'OK'


@patch('controller.materials_controller.sync_materials')
def test_get_materials_sync_validation_error(mock_sync_materials, client):
    mock_sync_materials.side_effect = BadRequestError("Error")

    response = client.get('/materials_sync')

    mock_sync_materials.assert_called_once_with()

    data = response.get_json()
    assert response.status_code == 400
    assert data['status'] == 'error'


@patch('controller.materials_controller.dump_adsorbents')
@patch('controller.materials_controller.get_all_adsorbents')
@patch('controller.materials_controller.dump_adsorbates')
@patch('controller.materials_controller.get_all_adsorbates')
def test_get_adsorption_materials(mock_get_all_adsorbates, mock_dump_adsorbates,
                                  mock_get_all_adsorbents, mock_dump_adsorbents, client):

    adsorbate_data = [{'id': 1, 'ion_name': 'Carbon', 'iupac_name': 'C', 'formula': 'CO2'}]
    adsorbent_data = [{'id': 1, 'name': 'Metal'}]

    mock_get_all_adsorbates.return_value = adsorbate_data
    mock_dump_adsorbates.return_value = adsorbate_data
    mock_get_all_adsorbents.return_value = adsorbent_data
    mock_dump_adsorbents.return_value = adsorbent_data

    response = client.get('/adsorption-materials')

    mock_get_all_adsorbates.assert_called_once_with()
    mock_dump_adsorbates.assert_called_once_with(adsorbate_data)
    mock_get_all_adsorbents.assert_called_once_with()
    mock_dump_adsorbents.assert_called_once_with(adsorbent_data)

    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'adsorbates' in data
    assert 'adsorbents' in data
    assert len(data['adsorbates']) == len(adsorbate_data)
    assert len(data['adsorbents']) == len(adsorbent_data)