"""ABE-004: validation and normalization of new adsorbates and adsorbents."""
import pytest
from marshmallow import ValidationError

from entities.schemas.adsorbate_schema import (
    ADSORBATE_CREATION_SCHEMA, MAX_FORMULA, MAX_ION_NAME, MAX_IUPAC_NAME,
)
from entities.schemas.adsorbent_schema import ADSORBENT_CREATION_SCHEMA, MAX_NAME


def adsorbate(**overrides):
    payload = {"ion_name": "mercurio", "iupac_name": "mercurio (II)", "formula": "Hg"}
    payload.update(overrides)
    return payload


def test_should_load_a_valid_adsorbate():
    """KMAT-H02"""
    assert ADSORBATE_CREATION_SCHEMA.load(adsorbate()) == adsorbate()


def test_should_trim_and_collapse_spaces():
    """KMAT-H03"""
    loaded = ADSORBATE_CREATION_SCHEMA.load(adsorbate(ion_name="  mercurio   total ", formula=" Hg "))

    assert loaded["ion_name"] == "mercurio total"
    assert loaded["formula"] == "Hg"


def test_should_keep_the_case_as_typed():
    """KMAT-E01: case only matters for duplicates, the stored text is the user's"""
    assert ADSORBENT_CREATION_SCHEMA.load({"name": "Carbón Activado"})["name"] == "Carbón Activado"


@pytest.mark.parametrize("field", ["ion_name", "iupac_name", "formula"])
def test_should_require_every_adsorbate_field(field):
    """KMAT-N04"""
    payload = adsorbate()
    del payload[field]

    with pytest.raises(ValidationError) as error:
        ADSORBATE_CREATION_SCHEMA.load(payload)

    assert field in error.value.messages


@pytest.mark.parametrize("value", ["", "   ", None, 12, ["Hg"]])
def test_should_reject_empty_blank_or_non_string_values(value):
    """KMAT-N05: blank is empty after trimming"""
    with pytest.raises(ValidationError) as error:
        ADSORBATE_CREATION_SCHEMA.load(adsorbate(formula=value))

    assert "formula" in error.value.messages


@pytest.mark.parametrize("field, limit", [
    ("ion_name", MAX_ION_NAME), ("iupac_name", MAX_IUPAC_NAME), ("formula", MAX_FORMULA),
])
def test_should_accept_the_limit_and_reject_one_more(field, limit):
    """KMAT-B01: the limits are the column sizes"""
    assert ADSORBATE_CREATION_SCHEMA.load(adsorbate(**{field: "x" * limit}))[field] == "x" * limit

    with pytest.raises(ValidationError) as error:
        ADSORBATE_CREATION_SCHEMA.load(adsorbate(**{field: "x" * (limit + 1)}))

    assert field in error.value.messages


def test_should_count_the_limit_after_trimming():
    """KMAT-B02"""
    assert ADSORBENT_CREATION_SCHEMA.load({"name": "  " + "x" * MAX_NAME + "  "})["name"] == "x" * MAX_NAME


def test_should_reject_a_too_long_adsorbent_name():
    """KMAT-B03"""
    with pytest.raises(ValidationError):
        ADSORBENT_CREATION_SCHEMA.load({"name": "x" * (MAX_NAME + 1)})


def test_should_reject_unknown_fields():
    """KMAT-N06: the id comes from the database, never from the client"""
    with pytest.raises(ValidationError) as error:
        ADSORBENT_CREATION_SCHEMA.load({"name": "Zeolita", "id": 99})

    assert "id" in error.value.messages
