import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from marshmallow.exceptions import ValidationError

from app import db
from database import Sample
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from services.investigation_service import excecute_linearizations, add_investigation_db

blueprint = Blueprint('investigation', __name__)


@blueprint.route('/investigation', methods=['POST'])
def create_investigation():
    try:
        request_json = request.get_json()

        if 'ce' and 'qe' not in request_json:
            msg = f"Bad Request: ce and qe are required"
            return jsonify({"status": "ERROR", "message": msg}), HTTPStatus.BAD_REQUEST

        sample_data = SAMPLE_SCHEMA.load(request_json)
        sample = Sample(ce=sample_data.ce, qe=sample_data.qe)
        db.session.add(sample)
        db.session.commit()
        result = add_investigation_db(sample)

        return jsonify(result), HTTPStatus.CREATED

    except ValidationError as me:
        msg = f"Input validation error: {me}"
        logging.error(msg, exc_info=me)
        db.session.rollback()
        return {"message": msg}, HTTPStatus.BAD_REQUEST


@blueprint.route('/investigation/sample', methods=['POST'])
def create_investigation_with_sample():
    try:
        request_json = request.get_json()

        if 'sample_id' not in request_json:
            msg = f"Bad Request: sample_id is required"
            return jsonify({"status": "ERROR", "message": msg}), HTTPStatus.BAD_REQUEST

        sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=request_json["sample_id"]).first()
        if not sample:
            msg = f"Sample with {request_json['sample_id']} doesn't exist"
            return jsonify({"status": "ERROR", "message": msg}), HTTPStatus.NOT_FOUND

        result = add_investigation_db(sample)

        return jsonify(result), HTTPStatus.CREATED

    except ValidationError as me:
        msg = f"Input validation error: {me}"
        logging.error(msg, exc_info=me)
        db.session.rollback()
        return {"message": msg}, HTTPStatus.BAD_REQUEST


@blueprint.route('/investigation/run-linearization', methods=['POST'])
def run_investigation_model():
    try:
        response = {"investigation_id": request.json['investigation_id'], "results": []}
        request_json = request.get_json()
        for model in request_json["models"]:
            model_result = excecute_linearizations(request_json['investigation_id'], model.get('linearizations', []),
                                               model["model"])
            response["results"].append(model_result)

        return jsonify(response), HTTPStatus.OK
    except Exception as me:
        msg = f"Error running linealization: {me}"
        logging.error(msg, exc_info=me)
        return {"message": msg}, HTTPStatus.BAD_REQUEST