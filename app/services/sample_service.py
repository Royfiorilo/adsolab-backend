from marshmallow import ValidationError

from app import db
from datetime import datetime
from database import Sample, User
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from exceptions.exceptions import NotFoundError, FilterSampleError, BadRequestError
from services.materials_service import find_adsorbent, find_adsorbate


def find_sample(sample_id):
    sample = Sample.with_schema(SAMPLE_SCHEMA).filter_by(sample_id=sample_id, deleted_at=None).first()
    if not sample:
        raise NotFoundError(f"Sample with id {sample_id} doesn't exist")
    return sample

def get_all_samples():
    samples = Sample.with_schema(None).filter_by(deleted_at=None).all()
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
        user = User.query.filter_by(id=sample_data.user_id).first()
        name  = user.email.split("@")[0]
        adsobate_name = find_adsorbate(sample_data.adsorbate_id).ion_name
        adsorbent_name = find_adsorbent(sample_data.adsorbent_id).name
        title = sample_data.create_sample_name(name, adsobate_name, adsorbent_name)

        sample = Sample(ce=x, qe =y,
                        title=title,
                        description=sample_data.description,
                        temperature=sample_data.temperature,
                        measure_unit=sample_data.measure_unit,
                        adsorbent_id=sample_data.adsorbent_id,
                        adsorbate_id=sample_data.adsorbate_id,
                        user_id=sample_data.user_id )
        db.session.add(sample)
        db.session.commit()
        return sample
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")


def delete_sample(sample_id):
    find_sample(sample_id)
    sample = db.session.query(Sample).filter_by(sample_id=sample_id).first()
    sample.deleted_at = datetime.utcnow()
    db.session.commit()