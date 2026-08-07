"""
kinetics_investigation_service.py

Responsabilidad:
    Coordinar el flujo completo de una investigación cinética:
      - Predicción de semillas iniciales.
      - Ejecución del ajuste no lineal.
      - Ejecución de linealizaciones (opcional, iteración futura).
      - Guardado y recuperación del histórico de versiones.
      - Listado paginado de investigaciones.

    Equivalente a `investigation_service.py` del módulo de equilibrio, pero
    operando exclusivamente sobre entidades cinéticas.
"""
from app import db
from database import KineticInvestigation, KineticSample
from entities.schemas.kinetics_investigation_schema import KINETICS_INVESTIGATION_SCHEMA
from exceptions.exceptions import NotFoundError, ForbiddenError, BadRequestError
from services.kinetics_no_linear_model_service import predict_kinetic_seeds, run_kinetic_no_linear_models
from services.kinetics_version_service import (
    save_kinetic_version, get_kinetic_version, get_kinetic_versions, delete_kinetic_version
)


# ---------------------------------------------------------------------------
# Investigation CRUD
# ---------------------------------------------------------------------------

def create_kinetic_investigation(kinetic_sample_id: int, user_id: int):
    """
    Crea una investigación cinética nueva para una muestra dada, o devuelve
    la existente si ya existe una para ese par (muestra, usuario).
    """
    existing = (
        db.session.query(KineticInvestigation)
        .filter_by(kinetic_sample_id=kinetic_sample_id, user_id=user_id)
        .first()
    )
    if existing:
        return existing

    investigation = KineticInvestigation(
        kinetic_sample_id=kinetic_sample_id,
        user_id=user_id,
    )
    db.session.add(investigation)
    db.session.commit()
    return investigation


def get_kinetic_investigations(page: int, per_page: int, user_id: int = None):
    """Lista investigaciones cinéticas paginadas, opcionalmente filtradas por usuario."""
    query = db.session.query(KineticInvestigation)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)

    total = query.count()
    investigations = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "investigations": investigations,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    }


def delete_kinetic_investigation(kinetic_investigation_id: int, user_id: int):
    """Elimina una investigación cinética y sus versiones en cascada."""
    investigation = db.session.query(KineticInvestigation).filter_by(
        kinetic_investigation_id=kinetic_investigation_id
    ).first()
    if investigation is None:
        raise NotFoundError(f"Kinetic investigation {kinetic_investigation_id} not found.")
    if investigation.user_id != user_id:
        raise ForbiddenError("User is not authorized to delete this kinetic investigation.")
    db.session.delete(investigation)
    db.session.commit()


# ---------------------------------------------------------------------------
# Analysis workflow
# ---------------------------------------------------------------------------

def run_kinetics_predict_seeds(request_json: dict):
    """Wrapper para predicción de semillas cinéticas (delega al service de ajuste)."""
    return predict_kinetic_seeds(request_json)


def run_kinetics_no_linear(request_json: dict):
    """
    Orquesta ajuste no lineal cinético + comparación.

    TODO: delegará a `run_kinetic_no_linear_models` y `get_kinetic_comparison`
    una vez implementados.
    """
    return run_kinetic_no_linear_models(request_json)


# ---------------------------------------------------------------------------
# Version management (delegated to kinetics_version_service)
# ---------------------------------------------------------------------------

def validate_and_save_kinetic_version(request_json: dict, user_id: int):
    """
    Valida permisos y guarda una versión de investigación cinética.

    Si `kinetic_investigation_id` es None, crea una investigación nueva.
    """
    kinetic_sample_id = request_json.get('kinetic_sample_id')
    kinetic_investigation_id = request_json.get('kinetic_investigation_id')

    if kinetic_investigation_id is None:
        investigation = create_kinetic_investigation(kinetic_sample_id, user_id)
        kinetic_investigation_id = investigation.kinetic_investigation_id
    else:
        investigation = db.session.query(KineticInvestigation).filter_by(
            kinetic_investigation_id=kinetic_investigation_id
        ).first()
        if investigation is None:
            raise NotFoundError(f"Kinetic investigation {kinetic_investigation_id} not found.")
        if investigation.user_id != user_id:
            raise ForbiddenError("User is not authorized to save this kinetic investigation.")

    version = save_kinetic_version(
        kinetic_investigation_id=kinetic_investigation_id,
        results=request_json.get('results', []),
        comparison=request_json.get('comparison', {}),
        iterations=request_json.get('iterations'),
        steps=request_json.get('steps'),
    )
    return {
        "status": "ok",
        "kinetic_investigation_id": kinetic_investigation_id,
        "version_id": version.version_id,
    }
