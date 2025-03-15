import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from jsonschema.exceptions import ValidationError

from entities.schemas.sample_schema import SAMPLE_SCHEMA
from exceptions.exceptions import BadRequestError
from services.sample_service import get_all_samples, find_sample, create_sample_db, delete_sample

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
def create_sample():
    try:
        request_json = request.get_json()
        sample = create_sample_db(request_json)
        result = SAMPLE_SCHEMA.dump(sample)
        return jsonify(result), HTTPStatus.CREATED
    except ValidationError as me:
        BadRequestError(f"Validation Error: {me}")


@blueprint.route('/sample/<int:sample_id>', methods=['DELETE'])
def delete(sample_id):

    try:
        delete_sample(sample_id)
    except Exception as e:
        raise e
    response = {
        "sample_id": sample_id
    }
    return response, HTTPStatus.OK
