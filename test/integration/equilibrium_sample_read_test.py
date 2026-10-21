"""Reading equilibrium samples with their adsorbate and adsorbent names, on PostgreSQL."""
import pytest

from database import Adsorbate, Adsorbent, Sample
from entities.schemas.sample_schema import SAMPLE_SCHEMA
from services.sample_service import find_sample

pytestmark = pytest.mark.integration

SEEDED_MATERIAL_ID = 1


@pytest.fixture
def equilibrium_sample(db_session, make_user):
    sample = Sample(
        ce=[0.5, 1.0, 2.0], qe=[1.2, 2.0, 2.9], title="equilibrium sample",
        adsorbate_id=SEEDED_MATERIAL_ID, adsorbent_id=SEEDED_MATERIAL_ID, user_id=make_user().id,
    )
    db_session.add(sample)
    db_session.flush()
    return sample


def test_should_read_an_equilibrium_sample(equilibrium_sample):
    read = find_sample(equilibrium_sample.sample_id)

    assert read.ce == [0.5, 1.0, 2.0]


def test_should_include_material_names_when_reading_an_equilibrium_sample(db_session, equilibrium_sample):
    dumped = SAMPLE_SCHEMA.dump(find_sample(equilibrium_sample.sample_id))

    assert dumped["adsorbate"] == db_session.get(Adsorbate, SEEDED_MATERIAL_ID).iupac_name
    assert dumped["adsorbent"] == db_session.get(Adsorbent, SEEDED_MATERIAL_ID).name
