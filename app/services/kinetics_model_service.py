"""
kinetics_model_service.py

Responsabilidad:
    Consultar y exponer los modelos cinéticos disponibles en base de datos.
    Equivalente a `model_service.py` del módulo de equilibrio, pero filtrando
    la tabla `kinetic_model` en lugar de `model`.
"""
from database import db, KineticModel
from entities.schemas.kinetics_model_schema import KINETICS_MODEL_SCHEMA
from exceptions.exceptions import NotFoundError


def find_kinetic_models():
    """Devuelve todos los modelos cinéticos disponibles."""
    models = db.session.query(KineticModel).all()
    return [KINETICS_MODEL_SCHEMA.dump(m) for m in models]


def find_kinetic_model(model_id: int):
    """Devuelve un modelo cinético por ID. Lanza NotFoundError si no existe."""
    model = db.session.query(KineticModel).filter_by(_id=model_id).first()
    if model is None:
        raise NotFoundError(f"Kinetic model with id {model_id} not found.")
    return KINETICS_MODEL_SCHEMA.dump(model)
