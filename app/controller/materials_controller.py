import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from jsonschema.exceptions import ValidationError

from entities.schemas.adsorbate_schema import ADSORBATE_SCHEMA
from entities.schemas.adsorbent_schema import ADSORBENT_SCHEMA
from services.materials_service import get_all_adsorbents, get_all_adsorbates, sync_materials, dump_adsorbates, dump_adsorbents
from exceptions.exceptions import BadRequestError

blueprint = Blueprint('materials', __name__)


@blueprint.route('/adsorbates', methods=['GET'])
def get_adsorbates():
    adsorbates = get_all_adsorbates()

    output = dump_adsorbates(adsorbates)

    response = {'adsorbates': output}
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/adsorbents', methods=['GET'])
def get_adsorbents():
    adsorbents = get_all_adsorbents()
    output = dump_adsorbents(adsorbents)

    response = {'adsorbents': output}
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/materials_sync', methods=['GET'])
def get_materials_sync():
    try:
        sync_materials()
        response = {'message': 'Materials syncronized','status':'OK'}
        return jsonify(response), HTTPStatus.OK
    except ValidationError as me:
        BadRequestError(f"{me}")

@blueprint.route('/adsorption-materials', methods=['GET'])
def get_adsorption_materials():
    adsorbates = get_all_adsorbates()
    adsorbents = get_all_adsorbents()

    adsorbents = dump_adsorbents(adsorbents)
    adsorbates = dump_adsorbates(adsorbates)

    response = {'adsorbates': adsorbates, 'adsorbents': adsorbents}
    return jsonify(response), HTTPStatus.OK