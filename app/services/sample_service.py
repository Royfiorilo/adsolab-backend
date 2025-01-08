from marshmallow import ValidationError

from database import Sample
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from app import db
from exceptions.exceptions import NotFoundError, BadRequestError, FilterSampleError
from services.materials_service import find_adsorbate, find_adsorbent

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

def order_sample(ce, qe):
    pears = sorted(zip(ce, qe))
    x, y= zip(*pears)
    return list(x), list(y)

def filter_sample(sample, filter):
    if not filter:
        return sample
    if sample.len() < len(filter):
        raise FilterSampleError("The number of items to filter is greater than the sample.")
    if sample.len() <= max(filter) or min(filter) < 0:
        raise FilterSampleError("An index is outside the sample range.")

    return sample.remove(filter)


def create_sample_db(request_json):
    try:
        sample_data = SAMPLE_SCHEMA.load(request_json)
        x,y = order_sample(ce=sample_data.ce, qe= sample_data.qe)
        sample = Sample(ce=x, qe =y,
                        title=sample_data.title,
                        description=sample_data.description,
                        temperature=sample_data.temperature,
                        measure_unit=sample_data.measure_unit,
                        adsorbent_id=sample_data.adsorbent_id,
                        adsorbate_id=sample_data.adsorbate_id)
        db.session.add(sample)
        db.session.commit()
        return sample
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")
