from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_security import auth_required

from services.materials_service import get_all_adsorbents, get_all_adsorbates, dump_adsorbates, \
    dump_adsorbents, create_adsorbate, create_adsorbent

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


@blueprint.route('/adsorbates', methods=['POST'])
@auth_required()
def post_adsorbate():
    """Crea un adsorbato; 409 con el existente si ya hay uno con el mismo nombre de ion."""
    return jsonify(create_adsorbate(request.get_json(silent=True))), HTTPStatus.CREATED


@blueprint.route('/adsorbents', methods=['POST'])
@auth_required()
def post_adsorbent():
    """Crea un adsorbente; 409 con el existente si ya hay uno con el mismo nombre."""
    return jsonify(create_adsorbent(request.get_json(silent=True))), HTTPStatus.CREATED


@blueprint.route('/adsorption-materials', methods=['GET'])
def get_adsorption_materials():
    adsorbates = get_all_adsorbates()
    adsorbents = get_all_adsorbents()

    adsorbents = dump_adsorbents(adsorbents)
    adsorbates = dump_adsorbates(adsorbates)

    response = {'adsorbates': adsorbates, 'adsorbents': adsorbents}
    return jsonify(response), HTTPStatus.OK
