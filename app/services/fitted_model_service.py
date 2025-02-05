import logging

from marshmallow import ValidationError

from app import db
from database import FittedModel, Version, Comparison
from entities.historic import FittedMethod
from entities.schemas.historic_schema import VERSION_SCHEMA, FittedMethodSchema, FITTED_METHOD_SCHEMA


def create_version(request_json):
    try:
        version = VERSION_SCHEMA.load(request_json)
    except ValidationError as e:
        raise e
    return version

def insert_version(version_data):
    try:
        version = Version(investigation_id=version_data.investigation_id,
                          iterations=version_data.iterations,
                          steps=version_data.steps,
                          seeds=version_data.seeds,
                          created_at=version_data.created_at
                          )

        db.session.add(version)
        return version
    except Exception as e:
        db.session.rollback()
        logging.error("Error saving version: {}".format(e))
        raise e


def save_version(version_data):
    try:
        version = insert_version(version_data)
        fitted_models = []

        for fitted in version_data.fitted_models:
            fitted_methods = [
                FITTED_METHOD_SCHEMA.dump(fitted_method)
                for fitted_method in fitted.adjustment_methods
            ]

            fitted_model = FittedModel(model_id=fitted.model_id,
                                       best_adjust=fitted.best_adjust,
                                       adjustment_methods= fitted_methods,
                                       version_id= version.version_id)
            fitted_models.append(fitted_model)

        comparison = Comparison(heuristic=version_data.comparison.heuristic,
                                ml=version_data.comparison.ml,
                                version_id = version.version_id)
        db.session.add(version)
        db.session.add_all(fitted_models)
        db.session.add(comparison)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error("Error saving version: {}".format(e))
        raise e

