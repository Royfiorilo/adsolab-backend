"""The sample responses carry the adsorbate and adsorbent names, on PostgreSQL."""
import pytest

from database import Adsorbate, Adsorbent
from entities.schemas.kinetics_sample_schema import KINETICS_SAMPLE_SCHEMA
from services.kinetics_sample_service import find_readable_kinetic_sample, get_all_kinetic_samples

pytestmark = pytest.mark.integration


def test_should_include_material_names_when_reading_a_sample(db_session, make_kinetic_sample):
    sample = make_kinetic_sample()

    dumped = KINETICS_SAMPLE_SCHEMA.dump(find_readable_kinetic_sample(sample.kinetic_sample_id))

    assert dumped["adsorbate"] == db_session.get(Adsorbate, sample.adsorbate_id).iupac_name
    assert dumped["adsorbent"] == db_session.get(Adsorbent, sample.adsorbent_id).name


def test_should_include_material_names_when_listing_samples(db_session, make_kinetic_sample, make_user):
    user = make_user()
    make_kinetic_sample(user_id=user.id)

    dumped = [KINETICS_SAMPLE_SCHEMA.dump(sample) for sample in get_all_kinetic_samples(user.id)]

    assert dumped[0]["adsorbate"] is not None
    assert dumped[0]["adsorbent"] is not None


def test_should_return_no_names_when_the_sample_has_no_materials():
    dumped = KINETICS_SAMPLE_SCHEMA.dump({"time": [0, 1], "qt": [0, 1]})

    assert dumped["adsorbate"] is None
    assert dumped["adsorbent"] is None
