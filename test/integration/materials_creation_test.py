"""ABE-004: creating adsorbates and adsorbents on PostgreSQL."""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from database import Adsorbate, Adsorbent
from exceptions.exceptions import BadRequestError, ConflictError
from services import materials_service
from services.materials_service import create_adsorbate, create_adsorbent, get_all_adsorbates, get_all_adsorbents

pytestmark = pytest.mark.integration


def adsorbate(**overrides):
    payload = {"ion_name": "mercurio", "iupac_name": "mercurio (II)", "formula": "Hg"}
    payload.update(overrides)
    return payload


def count(session, model):
    return session.query(model).count()


def test_should_create_an_adsorbate_with_an_id_from_the_database(db_session):
    """KMAT-H04"""
    created = create_adsorbate(adsorbate())

    assert created["id"] is not None
    assert db_session.get(Adsorbate, created["id"]).ion_name == "mercurio"


def test_should_store_the_normalized_text(db_session):
    """KMAT-H05"""
    created = create_adsorbent({"name": "  Cáscara   de nuez "})

    assert db_session.get(Adsorbent, created["id"]).name == "Cáscara de nuez"


def test_should_list_a_created_material(db_session):
    """KMAT-H06"""
    created_adsorbate = create_adsorbate(adsorbate())
    created_adsorbent = create_adsorbent({"name": "Cáscara de nuez"})

    assert created_adsorbate["id"] in {row.id for row in get_all_adsorbates()}
    assert created_adsorbent["id"] in {row.id for row in get_all_adsorbents()}


def test_should_let_a_sample_use_a_created_material(db_session, make_kinetic_sample):
    """KMAT-H07"""
    created_adsorbate = create_adsorbate(adsorbate())
    created_adsorbent = create_adsorbent({"name": "Cáscara de nuez"})

    sample = make_kinetic_sample(adsorbate_id=created_adsorbate["id"], adsorbent_id=created_adsorbent["id"])

    assert sample.kinetic_sample_id is not None


@pytest.mark.parametrize("name", ["Carbón activado", "carbón ACTIVADO", "  carbón   activado  "])
def test_should_answer_conflict_with_the_seeded_material_when_only_case_or_spacing_differ(db_session, name):
    """KMAT-N07: 'Carbón activado' comes from the seed migration"""
    before = count(db_session, Adsorbent)

    with pytest.raises(ConflictError) as error:
        create_adsorbent({"name": name})

    assert error.value.existing["name"] == "Carbón activado"
    assert count(db_session, Adsorbent) == before


def test_should_answer_conflict_for_an_adsorbate_with_the_same_ion_name(db_session):
    """KMAT-N08: other fields do not matter, the ion name identifies the adsorbate"""
    first = create_adsorbate(adsorbate())

    with pytest.raises(ConflictError) as error:
        create_adsorbate(adsorbate(ion_name="MERCURIO", iupac_name="otro", formula="Hg2"))

    assert error.value.existing["id"] == first["id"]


def test_should_answer_conflict_when_another_request_wins_the_race(db_session):
    """KMAT-S01: the duplicate check misses the row, the unique index of the migration catches it"""
    first = create_adsorbent({"name": "Zeolita"})

    with patch.object(materials_service, "_find_same", side_effect=[None, db_session.get(Adsorbent, first["id"])]):
        with pytest.raises(ConflictError) as error:
            create_adsorbent({"name": "ZEOLITA"})

    assert error.value.existing["id"] == first["id"]
    assert db_session.query(Adsorbent).filter(Adsorbent.name.ilike("zeolita")).count() == 1


def test_should_enforce_the_normalized_uniqueness_in_the_database(db_session):
    """KMAT-S02: the index exists even for writes that skip the service"""
    db_session.add(Adsorbent(name="Bentonita"))
    db_session.flush()
    db_session.add(Adsorbent(name=" BENTONITA "))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_should_reject_an_invalid_payload_before_touching_the_database(db_session):
    """KMAT-N09"""
    before = count(db_session, Adsorbate)

    with pytest.raises(BadRequestError) as error:
        create_adsorbate(adsorbate(formula="x" * 11))

    assert "formula" in error.value.message
    assert count(db_session, Adsorbate) == before
