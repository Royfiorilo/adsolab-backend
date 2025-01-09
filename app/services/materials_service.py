from marshmallow import ValidationError

from database import Adsorbate, Adsorbent
from entities.schemas.adsorbate_schema import ADSORBATE_SCHEMA
from entities.schemas.adsorbent_schema import ADSORBENT_SCHEMA
from app import db
from exceptions.exceptions import NotFoundError, BadRequestError
from services.reactorapp_service import get_adsorbents, get_adsorbates

def get_all_adsorbents():
    adsorbents = Adsorbent.with_schema(None).all()
    if not adsorbents:
        raise NotFoundError("No adsorbents found")
    return adsorbents


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


def sync_materials():
    try:
        reactor_adsorbents = get_adsorbents()
        add_adsorbents(reactor_adsorbents)
        reactor_adsorbates = get_adsorbates()
        add_adsorbates(reactor_adsorbates)
    except Exception as e:
        raise BadRequestError(str(e))


def add_adsorbates(adsorbates):

    for adsorbate_json in adsorbates:
        adsorbate_json = traslate_adsorbate(adsorbate_json)
        adsorbate_data = ADSORBATE_SCHEMA.load(adsorbate_json)
        adsorbate = Adsorbate.with_schema(ADSORBATE_SCHEMA).filter_by(id=adsorbate_data.id).first()
        if not adsorbate:
            create_adsorbate(adsorbate_data)


def create_adsorbate(adsorbate_data):
    try:
        adsorbate = Adsorbate(id=adsorbate_data.id,
                           ion_name = adsorbate_data.ion_name,
                           IUPAC_name = adsorbate_data.IUPAC_name,
                           formula = adsorbate_data.formula)
        db.session.add(adsorbate)
        db.session.commit()
        return adsorbate
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")


def add_adsorbents(adsorbents):
    for adsorbent_json in adsorbents:
        adsorbent_json = traslate_adsorbent(adsorbent_json)
        adsorbent_data = ADSORBENT_SCHEMA.load(adsorbent_json)
        adsorbent = Adsorbent.with_schema(ADSORBENT_SCHEMA).filter_by(id=adsorbent_data.id).first()
        if not adsorbent:
            create_adsorbent(adsorbent_data)


def create_adsorbent(adsorbent_data):
    try:
        adsorbent = Adsorbent(id=adsorbent_data.id,
                              name=adsorbent_data.name
                              )
        db.session.add(adsorbent)
        db.session.commit()
        return adsorbent
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")

def traslate_adsorbate(json):
    return {
        'id' : json['id'],
        'ion_name': json['nombreIon'],
        'IUPAC_name': json['nombreIUPAC'],
        'formula': json['formula']
    }

def traslate_adsorbent(json):
    return {
        'id' : json['id'],
        'name': json['nombre']
    }