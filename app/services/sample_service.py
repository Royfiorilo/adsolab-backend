from marshmallow import ValidationError

from database import Sample
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from app import db
from exceptions.exceptions import NotFoundError, BadRequestError


def find_sample(sample_id):
    sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=sample_id).first()
    if not sample:
        raise NotFoundError(f"Sample with {sample_id} doesn't exist")
    return sample

def get_all_samples():
    samples = Sample.with_schema(None).all()
    if not samples:
        raise NotFoundError("No samples found")
    return samples

def create_sample_db(request_json):
    try:
        sample_data = SAMPLE_SCHEMA.load(request_json)
        sample = Sample(ce=sample_data.ce, qe= sample_data.qe)
        db.session.add(sample)
        db.session.commit()
        return sample
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")
