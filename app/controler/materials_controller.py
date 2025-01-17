import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from entities.schemas.adsorbate_schema import ADSORBATE_SCHEMA
from entities.schemas.adsorbent_schema import ADSORBENT_SCHEMA
from services.materials_service import get_all_adsorbents, get_all_adsorbates, sync_materials
from exceptions.exceptions import BadRequestError

blueprint = Blueprint('materials', __name__)


@blueprint.route('/adsorbates', methods=['GET'])
def get_adsorbates():
    adsorbates = get_all_adsorbates()
    output = []

    for adsorbate in adsorbates:
        adsorbate_json = ADSORBATE_SCHEMA.dump(adsorbate)
        output.append(adsorbate_json)

    response = {'adsorbates': output}
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/adsorbents', methods=['GET'])
def get_adsorbents():
    adsorbents = get_all_adsorbents()
    output = []

    for adsorbent in adsorbents:
        adsorbent_json = ADSORBENT_SCHEMA.dump(adsorbent)
        output.append(adsorbent_json)

    response = {'adsorbents': output}
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/materials_sync', methods=['GET'])
def get_materials_sync():
    sync_materials()
    response = {'message': 'Materials syncronized','status':'OK'}
    return jsonify(response), HTTPStatus.OK