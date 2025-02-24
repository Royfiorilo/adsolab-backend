import logging

from marshmallow import ValidationError

from app import db
from database import FittedModel, Version, Comparison
from entities.comparator import AdsorptionModelComparison
from entities.no_linear_model import  AdsorptionPredictor
from entities.schemas.historic_schema import VERSION_SCHEMA, FITTED_METHOD_SCHEMA
from exceptions.exceptions import NotFoundError
from services.model_service import find_model


def create_version(request_json):
    try:
        version = VERSION_SCHEMA.load(request_json)
    except ValidationError as e:
        raise e
    return version

def is_valid_version(investigation_id, version_id):
    return Version.with_schema(None).filter_by(version_id=version_id, investigation_id=investigation_id).count() > 0


def save_version(version_data):
    try:
        last_version = Version.with_schema(None).filter_by(investigation_id=version_data.investigation_id).order_by(
            Version.version_id.desc()).first()
        next_version_id = (last_version.version_id + 1) if last_version else 1
        version = Version(investigation_id=version_data.investigation_id,
                          iterations=version_data.iterations,
                          steps=version_data.steps,
                          created_at=version_data.created_at,
                          version_id=next_version_id
                          )

        fitted_models = []

        for fitted in version_data.fitted_models:
            fitted_methods = [
                FITTED_METHOD_SCHEMA.dump(fitted_method)
                for fitted_method in fitted.adjustment_methods
            ]

            fitted_model = FittedModel(model_id=fitted.model_id,
                                       best_adjust=fitted.best_adjust,
                                       adjustment_methods= fitted_methods,
                                       seeds = fitted.seeds,
                                       version_id= next_version_id, investigation_id=version_data.investigation_id)
            fitted_models.append(fitted_model)

        comparison = Comparison(heuristic=version_data.comparison.heuristic,
                                ml=version_data.comparison.ml,
                                version_id = next_version_id, investigation_id=version_data.investigation_id)

        db.session.add(version)
        db.session.add_all(fitted_models)
        db.session.add(comparison)

        db.session.commit()
        return version
    except Exception as e:
        db.session.rollback()
        logging.error("Error saving version: {}".format(e))
        raise e


def validate_and_get_version(version_id, investigation):
    try:
        investigation_id = investigation.investigation_id
        if not is_valid_version(investigation_id, version_id):
            raise NotFoundError(f"Investigation with ID {investigation_id} not found")

        version = Version.with_schema(VERSION_SCHEMA).filter_by(
            investigation_id=investigation_id, version_id=version_id
        ).first()

        qe_preds, qe_preds_extended = process_fitted_models(version.fitted_models, investigation)

        version.comparison.ml = AdsorptionModelComparison.get_ml_coefs_models(
            investigation.sample.qe, qe_preds, qe_preds_extended
        )

        return version.to_dict()
    except ValidationError as e:
        logging.error(f"Error recovering version: {e}")


def process_fitted_models(fitted_models, investigation):
    ce_values = investigation.sample.ce
    constants = investigation.constants
    qe_preds, qe_preds_extended = [], []

    for fitted_model in fitted_models:
        model = find_model(model_id=fitted_model.model_id)
        if constants:
            model.formula.replace_constants(constants)
        points_extender = AdsorptionPredictor(model.formula)

        for fitted_method in fitted_model.adjustment_methods:
            params_dict = {p["name"]: p["value"] for p in fitted_method.params}
            x, y_extended = points_extender.predict(ce_values, params_dict)
            _, y = points_extender.predict(ce_values, params_dict)

            fitted_method.transformed = {"x": list(x), "y": list(y)}

            if fitted_method.name == fitted_model.best_adjust:
                _, qe_pred = points_extender.predict(ce_values, params_dict, False)
                qe_preds.append(list(qe_pred))
                qe_preds_extended.append(list(y))

    return qe_preds, qe_preds_extended


def get_versions_by_investigation(investigation_id):
    versions_by_investigation = Version.with_schema(VERSION_SCHEMA).filter_by(investigation_id=investigation_id)
    versions = []
    for version in versions_by_investigation:
        fitted_models = []
        comparision = version.comparison
        for fitted_model in version.fitted_models:
            fitted_models.append({
                "model_id": fitted_model.model_id,
                "best_adjust": fitted_model.best_adjust,
                "seeds": fitted_model.seeds
            })
        properties = {
            "version_id": version.version_id,
            "created_at": version.created_at,
            "best_model_heuristic": comparision.heuristic["best_model"],
            "best_model_ml": comparision.ml["best_model"],
            "fitted_models": fitted_models
        }
        versions.append(properties)
    return versions
