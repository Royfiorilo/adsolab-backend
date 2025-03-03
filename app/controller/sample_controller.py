import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify

from entities.schemas.sample_schema import SAMPLE_SCHEMA
from exceptions.exceptions import BadRequestError, NotFoundError
from services.sample_service import get_all_samples, find_sample, create_sample_db

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
    try:
        sample = find_sample(sample_id)
        result = SAMPLE_SCHEMA.dump(sample)
        return jsonify(result), HTTPStatus.OK
    except NotFoundError as e:
        raise e

@blueprint.route('/sample', methods=['POST'])
def create_sample():
    try:
        request_json = request.get_json()
        sample = create_sample_db(request_json)
        result = SAMPLE_SCHEMA.dump(sample)
        return jsonify(result), HTTPStatus.CREATED
    except BadRequestError as me:
        raise me

