from marshmallow import ValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from database import Adsorbate, Adsorbent
from entities.schemas.adsorbate_schema import ADSORBATE_SCHEMA, ADSORBATE_CREATION_SCHEMA
from entities.schemas.adsorbent_schema import ADSORBENT_SCHEMA, ADSORBENT_CREATION_SCHEMA
from app import db
from exceptions.exceptions import BadRequestError, ConflictError, NotFoundError

def get_all_adsorbents():
    adsorbents = Adsorbent.with_schema(None).all()
    if not adsorbents:
        raise NotFoundError("No adsorbents found")
    return adsorbents

def dump_adsorbents(adsorbents):
    dumps = []
    for adsorbent in adsorbents:
        adsorbent_json = ADSORBENT_SCHEMA.dump(adsorbent)
        dumps.append(adsorbent_json)
    return dumps

def dump_adsorbates(adsorbates):
    dumps = []
    for adsorbate in adsorbates:
        adsorbate_json = ADSORBATE_SCHEMA.dump(adsorbate)
        dumps.append(adsorbate_json)
    return dumps

def get_all_adsorbates():
    adsorbates = Adsorbate.with_schema(None).all()
    if not adsorbates:
        raise NotFoundError("No adsorbates found")
    return adsorbates

def find_adsorbate(adsorbate_id):
    adsorbate = Adsorbate.with_schema(ADSORBATE_SCHEMA).filter_by(id=adsorbate_id).first()
    if not adsorbate:
        raise NotFoundError(f"Adsorbate with {adsorbate_id} doesn't exist")
    return adsorbate

def find_adsorbent(adsorbent_id):
    adsorbent = Adsorbent.with_schema(ADSORBENT_SCHEMA).filter_by(id=adsorbent_id).first()
    if not adsorbent:
        raise NotFoundError(f"Adsorbent with {adsorbent_id} doesn't exist")
    return adsorbent


def _normalized(column):
    """Same normalization as the unique indexes of the migration: trim, collapse spaces, lowercase."""
    return func.lower(func.regexp_replace(func.btrim(column), r'\s+', ' ', 'g'))


def _load(schema, request_json):
    try:
        return schema.load(request_json if request_json is not None else {})
    except ValidationError as error:
        raise BadRequestError(f"Validation Error: {error.messages}")


def _find_same(model, column, value):
    return db.session.query(model).filter(_normalized(column) == value.lower()).first()


def _create(model, column, value, values, dump, kind):
    """Inserts unless a material with the same normalized name exists (409 with the existing one)."""
    existing = _find_same(model, column, value)
    if existing:
        raise ConflictError(f"The {kind} '{value}' already exists.", dump(existing))
    material = model(**values)
    db.session.add(material)
    try:
        db.session.commit()
    except IntegrityError:
        # Another request created it between the check and the insert: the unique index decides.
        db.session.rollback()
        existing = _find_same(model, column, value)
        if existing is None:
            raise
        raise ConflictError(f"The {kind} '{value}' already exists.", dump(existing))
    return material


def create_adsorbate(request_json):
    data = _load(ADSORBATE_CREATION_SCHEMA, request_json)
    adsorbate = _create(Adsorbate, Adsorbate.ion_name, data['ion_name'], data,
                        ADSORBATE_SCHEMA.dump, 'adsorbate')
    return ADSORBATE_SCHEMA.dump(adsorbate)


def create_adsorbent(request_json):
    data = _load(ADSORBENT_CREATION_SCHEMA, request_json)
    adsorbent = _create(Adsorbent, Adsorbent.name, data['name'], data,
                        ADSORBENT_SCHEMA.dump, 'adsorbent')
    return ADSORBENT_SCHEMA.dump(adsorbent)
