"""
kinetics_sample_service.py

Responsabilidad:
    Validar, ordenar, calcular (qt desde concentración si aplica) y persistir
    muestras cinéticas. Equivalente a `sample_service.py` del módulo de
    equilibrio pero con la entidad `KineticSample` y la lógica propia de
    datos temporales (time/qt).
"""
from datetime import datetime

from marshmallow import ValidationError

from app import db
from database import KineticSample, User
from entities.schemas.kinetics_sample_schema import KINETICS_SAMPLE_SCHEMA
from exceptions.exceptions import NotFoundError, FilterSampleError, BadRequestError, ForbiddenError
from services.materials_service import find_adsorbate, find_adsorbent


def find_kinetic_sample(kinetic_sample_id: int):
    """Recupera una muestra cinética activa (no eliminada) por ID."""
    sample = (
        KineticSample.with_schema(KINETICS_SAMPLE_SCHEMA)
        .filter_by(kinetic_sample_id=kinetic_sample_id, deleted_at=None)
        .first()
    )
    if not sample:
        raise NotFoundError(f"Kinetic sample with id {kinetic_sample_id} doesn't exist.")
    return sample


def get_all_kinetic_samples():
    """Devuelve todas las muestras cinéticas activas."""
    samples = KineticSample.with_schema(None).filter_by(deleted_at=None).all()
    if not samples:
        raise NotFoundError("No kinetic samples found.")
    return samples


def order_sample(time, qt):
    """Ordena time/qt de menor a mayor tiempo."""
    pairs = sorted(zip(time, qt))
    t, q = zip(*pairs)
    return list(t), list(q)


def calculate_qt_from_concentration(concentration, initial_concentration, volume, adsorbent_mass):
    """
    Calcula qt a partir de datos de concentración.

    Fórmula:  qt = (C0 - Ct) * V / m
      C0  = initial_concentration [mg/L]
      Ct  = concentration at time t [mg/L]
      V   = volume [L]
      m   = adsorbent_mass [g]
    """
    return [
        (initial_concentration - ct) * volume / adsorbent_mass
        for ct in concentration
    ]


def filter_kinetic_sample(sample, filter_indexes):
    """Elimina puntos por índice (filtrado de outliers)."""
    if not filter_indexes:
        return sample
    if sample.len() < len(filter_indexes):
        raise FilterSampleError("The number of items to filter is greater than the sample.")
    if sample.len() <= max(filter_indexes) or min(filter_indexes) < 0:
        raise FilterSampleError("An index is outside the sample range.")
    sample.remove(filter_indexes)
    return sample


def create_kinetic_sample_db(request_json: dict):
    """
    Valida y crea una nueva muestra cinética en base de datos.

    Si se recibe `concentration` en lugar de `qt`, convierte usando
    `calculate_qt_from_concentration`.
    """
    try:
        sample_data = KINETICS_SAMPLE_SCHEMA.load(request_json)

        # Calcular qt si solo se aportaron concentraciones
        if sample_data.qt is None and sample_data.concentration is not None:
            sample_data.qt = calculate_qt_from_concentration(
                sample_data.concentration,
                sample_data.initial_concentration,
                sample_data.volume,
                sample_data.adsorbent_mass,
            )

        time_sorted, qt_sorted = order_sample(sample_data.time, sample_data.qt)

        user = User.query.filter_by(id=sample_data.user_id).first()
        username = user.email.split("@")[0]
        adsorbate = find_adsorbate(sample_data.adsorbate_id)
        adsorbent = find_adsorbent(sample_data.adsorbent_id)
        title = (
            sample_data.title
            or sample_data.create_sample_name(username, adsorbate.ion_name, adsorbent.name)
        )

        kinetic_sample = KineticSample(
            time=time_sorted,
            qt=qt_sorted,
            concentration=sample_data.concentration,
            initial_concentration=sample_data.initial_concentration,
            volume=sample_data.volume,
            adsorbent_mass=sample_data.adsorbent_mass,
            title=title,
            description=sample_data.description,
            temperature=sample_data.temperature,
            time_unit=sample_data.time_unit,
            measure_unit=sample_data.measure_unit,
            adsorbate_id=sample_data.adsorbate_id,
            adsorbent_id=sample_data.adsorbent_id,
            user_id=sample_data.user_id,
        )
        db.session.add(kinetic_sample)
        db.session.commit()
        return kinetic_sample

    except ValidationError as e:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {e}")


def delete_kinetic_sample(kinetic_sample_id: int, user_id: int):
    """Soft-delete de una muestra cinética (sólo el propietario puede borrarla)."""
    sample = find_kinetic_sample(kinetic_sample_id)
    if sample.user_id != user_id:
        raise ForbiddenError("User is not authorized to delete this kinetic sample.")
    db_sample = db.session.query(KineticSample).filter_by(
        kinetic_sample_id=kinetic_sample_id
    ).first()
    db_sample.deleted_at = datetime.utcnow()
    db.session.commit()
