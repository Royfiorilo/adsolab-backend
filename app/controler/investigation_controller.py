import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from marshmallow.exceptions import ValidationError

from app import db
from app.database import Sample, Investigation, Linearization
from app.entities.schemas.investigation_schema import INVESTIGATION_SCHEMA, InvestigationSchema
from app.entities.schemas.sample_schema import SAMPLE_SCHEMA
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA

blueprint = Blueprint('investigation', __name__)


@blueprint.route('/investigation/sample', methods=['POST'])
def create_investigation():
    try:
        request_json = request.get_json()
        sample_data = SAMPLE_SCHEMA.load(request_json)

        sample = Sample(ce=sample_data.ce, qe=sample_data.qe)
        db.session.add(sample)
        db.session.commit() #necesito este commit para que me cree el sample_id

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
    request_json = request.get_json()

    investigation = Investigation.whith_screma(INVESTIGATION_SCHEMA).filer_by(investigation_id=request_json['investigation_id']).first()
    sample = Sample.whith_screma(SAMPLE_SCHEMA).filer_by(sample_id=investigation.sample_id).first()
    for model_name in request_json.get('linearizations', []):

        linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(name=model_name).first()
        linearization.run(sample)
