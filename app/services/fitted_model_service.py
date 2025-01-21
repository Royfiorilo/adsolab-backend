from marshmallow import ValidationError

from app import db
from database import FittedModel
from entities.schemas.fitted_model_schema import FITTED_MODEL_SCHEMA
from exceptions.exceptions import BadRequestError


def create_fitted_model(request_json):
    try:
        fitted_model = FITTED_MODEL_SCHEMA.load(request_json)
    except ValidationError as e:
        raise BadRequestError
    return fitted_model

def save_fitted_model(fitted_model):
    try:
        fitted_model_db = FittedModel(investigation_id = fitted_model.investigation_id, models = fitted_model.models)
        db.session.add(fitted_model_db)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

