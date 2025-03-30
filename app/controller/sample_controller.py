from http import HTTPStatus

from flask import Blueprint, request, jsonify
from flask_security import auth_required

from entities.schemas.sample_schema import SAMPLE_SCHEMA
from services.sample_service import get_all_samples, find_sample, create_sample_db, delete_sample
from flask_login import current_user
blueprint = Blueprint('sample', __name__)


@blueprint.route('/samples', methods=['GET'])
def get_samples():
    samples = get_all_samples()
    output = []

    for sample in samples:
        sample_json = SAMPLE_SCHEMA.dump(sample)
        output.append(sample_json)

    response = {'samples': output}
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/sample/<int:sample_id>', methods=['GET'])
def get_sample_by_id(sample_id):
    sample = find_sample(sample_id)
    result = SAMPLE_SCHEMA.dump(sample)
    return jsonify(result), HTTPStatus.OK


@blueprint.route('/sample', methods=['POST'])
@auth_required()
def create_sample():
    request_json = request.get_json()
    request_json['user_id'] = current_user.id
    sample = create_sample_db(request_json)
    result = SAMPLE_SCHEMA.dump(sample)
    return jsonify(result), HTTPStatus.CREATED


@blueprint.route('/sample/<int:sample_id>', methods=['DELETE'])
@auth_required()
def delete(sample_id):

    try:
        delete_sample(sample_id,current_user.id)
    except Exception as e:
        raise e
    response = {
        "sample_id": sample_id
    }
    return response, HTTPStatus.OK

