import json
from unittest.mock import patch

from exceptions.exceptions import BadRequestError, ConflictError


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


def test_should_not_expose_the_removed_reactorapp_sync(client):
    """KMAT-N01: the ReactorApp sync was removed"""
    response = client.get('/materials_sync')

    assert response.status_code == 404


@patch('controller.materials_controller.create_adsorbate')
def test_should_answer_201_with_the_created_adsorbate(mock_create, client):
    """KMAT-H01"""
    mock_create.return_value = {'id': 11, 'ion_name': 'mercurio', 'iupac_name': 'mercurio (II)', 'formula': 'Hg'}
    payload = {'ion_name': 'mercurio', 'iupac_name': 'mercurio (II)', 'formula': 'Hg'}

    response = client.post('/adsorbates', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == 201
    assert json.loads(response.data)['id'] == 11
    mock_create.assert_called_once_with(payload)


@patch('controller.materials_controller.create_adsorbent')
def test_should_answer_409_with_the_existing_adsorbent(mock_create, client):
    """KMAT-N02"""
    mock_create.side_effect = ConflictError("The adsorbent 'carbón activado' already exists.", {'id': 2, 'name': 'Carbón activado'})

    response = client.post('/adsorbents', data=json.dumps({'name': 'carbón activado'}), content_type='application/json')

    assert response.status_code == 409
    assert json.loads(response.data)['existing'] == {'id': 2, 'name': 'Carbón activado'}


@patch('controller.materials_controller.create_adsorbent')
def test_should_answer_400_when_the_payload_is_invalid(mock_create, client):
    """KMAT-N03"""
    mock_create.side_effect = BadRequestError("Validation Error: {'name': ['Missing data for required field.']}")

    response = client.post('/adsorbents', data='not json', content_type='application/json')

    assert response.status_code == 400
    mock_create.assert_called_once_with(None)
