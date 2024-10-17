import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from marshmallow.exceptions import ValidationError

from app import db
from database import Sample
from entities.schemas.sample_schema import SAMPLE_SCHEMA

blueprint = Blueprint('sample', __name__)

@blueprint.route('/samples', methods=['GET'])
def get_samples():
    samples = Sample.with_schema(None).all()

    if not samples:
        return jsonify({"status": "error", "message": "No samples found"}), HTTPStatus.NOT_FOUND

    output = []

    for sample in samples:
        sample_json = SAMPLE_SCHEMA.dump(sample)
        output.append(sample_json)

    response = {'samples': output}
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/sample', methods=['GET'])
def get_sample_by_id():
    try:
        request_json = request.get_json()
        sample_id = request_json['sample_id']
        sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=sample_id).first()
        if not sample:
            msg = f"Sample with {sample_id} doesn't exist"
            return jsonify({"status": "ERROR", "message": msg}), HTTPStatus.NOT_FOUND
        result = SAMPLE_SCHEMA.dump(sample)
        return jsonify(result), HTTPStatus.OK
    except Exception as e:
        logging.exception(e)
        return jsonify({"status": "ERROR", "message": str(e)}), HTTPStatus.BAD_REQUEST

@blueprint.route('/sample', methods=['POST'])
def create_sample():
    try:
        request_json = request.get_json()
        sample_data = SAMPLE_SCHEMA.load(request_json)

        sample = Sample(ce=sample_data.ce, qe=sample_data.qe)
        db.session.add(sample)
        db.session.commit()

        result = SAMPLE_SCHEMA.dump(sample)
        return jsonify(result), HTTPStatus.CREATED

    except ValidationError as me:
        msg = f"Input validation error: {me}"
        logging.error(msg, exc_info=me)
        db.session.rollback()
        return {"message": msg}, HTTPStatus.BAD_REQUEST
