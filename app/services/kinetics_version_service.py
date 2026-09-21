"""
kinetics_version_service.py

Responsabilidad:
    Persistir y recuperar versiones de investigaciones cinéticas.
    Equivalente a `version_service.py` del módulo de equilibrio, pero
    operando sobre las tablas `kinetic_version`, `kinetic_fitted_model` y
    `kinetic_comparison`.

    Diferencia clave con el módulo de equilibrio: `adjustment_methods` y
    `comparison.ml` cinéticos ya vienen con su curva `transformed` calculada
    por `kinetics_no_linear_model_service`/`kinetics_comparison_service`, así
    que se guardan y se devuelven tal cual (no hace falta recalcular las
    curvas contra la fórmula del modelo al leer una versión, como sí hace
    `version_service.process_fitted_models` en equilibrio).
"""
from flask import current_app

from app import db
from database import KineticComparison, KineticFittedModel, KineticInvestigation, KineticVersion
from exceptions.exceptions import BadRequestError, ForbiddenError, NotFoundError
from signals import version_deleted, version_saved

REQUIRED_RESULT_FIELDS = ("model", "best_adjust", "adjustment_methods")


def _get_kinetic_investigation(kinetic_investigation_id: int) -> KineticInvestigation:
    investigation = db.session.query(KineticInvestigation).filter_by(
        kinetic_investigation_id=kinetic_investigation_id
    ).first()
    if investigation is None:
        raise NotFoundError(f"Kinetic investigation {kinetic_investigation_id} not found.")
    return investigation


def _get_kinetic_version_row(kinetic_investigation_id: int, version_id: int) -> KineticVersion:
    version = db.session.query(KineticVersion).filter_by(
        kinetic_investigation_id=kinetic_investigation_id, version_id=version_id
    ).first()
    if version is None:
        raise NotFoundError(
            f"Kinetic investigation {kinetic_investigation_id} has no version {version_id}."
        )
    return version


def _validate_results(results: list):
    if not results:
        raise BadRequestError("At least one fitted model result is required to save a version.")
    for result in results:
        missing = [field for field in REQUIRED_RESULT_FIELDS if field not in result]
        if missing:
            raise BadRequestError(f"Missing fields in result: {', '.join(missing)}.")


def _validate_comparison(comparison: dict):
    if not comparison or not comparison.get("heuristic"):
        raise BadRequestError("comparison.heuristic is required to save a version.")


def save_kinetic_version(kinetic_investigation_id: int, results: list, comparison: dict,
                         iterations: int = None, steps: float = None) -> KineticVersion:
    """
    Crea y persiste una nueva versión de resultados cinéticos.

    El `version_id` es autoincremental por investigación (no global), igual
    que en el módulo de equilibrio.
    """
    _get_kinetic_investigation(kinetic_investigation_id)
    _validate_results(results)
    _validate_comparison(comparison)

    last_version = (
        db.session.query(KineticVersion)
        .filter_by(kinetic_investigation_id=kinetic_investigation_id)
        .order_by(KineticVersion.version_id.desc())
        .first()
    )
    next_version_id = (last_version.version_id + 1) if last_version else 1

    version = KineticVersion(
        kinetic_investigation_id=kinetic_investigation_id,
        version_id=next_version_id,
        iterations=iterations,
        steps=steps,
    )
    fitted_models = [
        KineticFittedModel(
            kinetic_model_id=result["model"],
            best_adjust=result["best_adjust"],
            adjustment_methods=result["adjustment_methods"],
            seeds=result.get("seeds", []),
            version_id=next_version_id,
            kinetic_investigation_id=kinetic_investigation_id,
        )
        for result in results
    ]
    comparison_row = KineticComparison(
        heuristic=comparison["heuristic"],
        ml=comparison.get("ml"),
        version_id=next_version_id,
        kinetic_investigation_id=kinetic_investigation_id,
    )

    try:
        db.session.add(version)
        db.session.add_all(fitted_models)
        db.session.add(comparison_row)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    if current_app:
        version_saved.send(current_app._get_current_object(), version=version)

    return version


def get_kinetic_version(kinetic_investigation_id: int, version_id: int) -> KineticVersion:
    """Recupera una versión cinética por ID de investigación y versión."""
    return _get_kinetic_version_row(kinetic_investigation_id, version_id)


def get_kinetic_versions(kinetic_investigation_id: int) -> list:
    """Lista todas las versiones de una investigación cinética, de más vieja a más nueva."""
    _get_kinetic_investigation(kinetic_investigation_id)
    return (
        db.session.query(KineticVersion)
        .filter_by(kinetic_investigation_id=kinetic_investigation_id)
        .order_by(KineticVersion.version_id.asc())
        .all()
    )


def delete_kinetic_version(kinetic_investigation_id: int, version_id: int, user_id: int):
    """
    Elimina una versión cinética. Solo el propietario de la investigación
    puede eliminarla. El borrado elimina en cascada sus fitted models y
    comparación (FK ondelete=CASCADE + relationship cascade).
    """
    investigation = _get_kinetic_investigation(kinetic_investigation_id)
    if investigation.user_id != user_id:
        raise ForbiddenError("User is not authorized to delete this kinetic investigation version.")

    version = _get_kinetic_version_row(kinetic_investigation_id, version_id)
    db.session.delete(version)
    db.session.commit()

    if current_app:
        version_deleted.send(
            current_app._get_current_object(),
            kinetic_investigation_id=kinetic_investigation_id,
            version_id=version_id,
        )
