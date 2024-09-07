import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from marshmallow.exceptions import ValidationError

from app import db
from database import Sample, Investigation
from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from services.investigation_service import excecute_linearizations

blueprint = Blueprint('investigation', __name__)


@blueprint.route('/investigation/sample', methods=['POST'])
def create_investigation():
    try:
        request_json = request.get_json()
        sample_data = SAMPLE_SCHEMA.load(request_json)

        sample = Sample(ce=sample_data.ce, qe=sample_data.qe)
        db.session.add(sample)
        db.session.commit()  # necesito este commit para que me cree el sample_id

        investigation = Investigation(sample_id=sample.sample_id)
        db.session.add(investigation)
        db.session.commit()

        result = INVESTIGATION_SCHEMA.dump(investigation)
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