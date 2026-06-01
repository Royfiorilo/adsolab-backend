"""
kinetics_version_service.py

Responsabilidad:
    Persistir y recuperar versiones de investigaciones cinéticas.
    Equivalente a `version_service.py` del módulo de equilibrio, pero
    operando sobre las tablas `kinetic_version`, `kinetic_fitted_model` y
    `kinetic_comparison`.

    TODO: implementar una vez que el ajuste no lineal cinético esté disponible
    y los schemas de guardado estén definidos.
"""
from app import db
from database import KineticVersion, KineticFittedModel, KineticComparison
from exceptions.exceptions import NotFoundError, ForbiddenError


def save_kinetic_version(kinetic_investigation_id: int, results: list, comparison: dict,
                         iterations: int = None, steps: float = None):
    """
    Crea y persiste una nueva versión de resultados cinéticos.

    TODO: implementar la lógica de serialización de `results` y `comparison`
    a filas de `kinetic_fitted_model` y `kinetic_comparison`.
    """
    raise NotImplementedError("save_kinetic_version: pending implementation.")


def get_kinetic_version(kinetic_investigation_id: int, version_id: int):
    """
    Recupera una versión cinética por ID de investigación y versión.
    Reconstruye curvas ajustadas y comparación ML.

    TODO: implementar.
    """
    raise NotImplementedError("get_kinetic_version: pending implementation.")


def get_kinetic_versions(kinetic_investigation_id: int):
    """
    Lista todas las versiones de una investigación cinética.

    TODO: implementar.
    """
    raise NotImplementedError("get_kinetic_versions: pending implementation.")


def delete_kinetic_version(kinetic_investigation_id: int, version_id: int, user_id: int):
    """
    Elimina una versión cinética. Solo el propietario de la investigación
    puede eliminarla.

    TODO: implementar.
    """
    raise NotImplementedError("delete_kinetic_version: pending implementation.")
