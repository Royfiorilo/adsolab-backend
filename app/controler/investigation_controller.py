import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from marshmallow.exceptions import ValidationError

from app import db
from app.database import Sample, Investigation
from app.entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from app.entities.schemas.sample_schema import SAMPLE_SCHEMA

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
