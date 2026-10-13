"""ABE-001: input validation of kinetic samples."""
import pytest
from marshmallow import ValidationError

from entities.schemas.kinetics_sample_schema import KINETICS_SAMPLE_SCHEMA


def valid_payload(**overrides):
    payload = {
        "time": [0, 5, 10, 20, 30],
        "concentration": [50, 40, 30, 25, 22],
        "initial_concentration": 50,
        "volume": 0.25,
        "adsorbent_mass": 0.5,
        "adsorbate_id": 1,
        "adsorbent_id": 2,
    }
    payload.update(overrides)
    return payload


def test_should_load_when_concentration_payload_is_valid():
    """KSAMPLE-H01"""
    sample = KINETICS_SAMPLE_SCHEMA.load(valid_payload())

    assert sample.concentration == [50, 40, 30, 25, 22]
    assert sample.volume == 0.25


@pytest.mark.parametrize("field", ["volume", "adsorbent_mass"])
@pytest.mark.parametrize("value", [0, -0.5])
def test_should_reject_non_positive_volume_or_mass(field, value):
    """KSAMPLE-N01"""
    with pytest.raises(ValidationError) as error:
        KINETICS_SAMPLE_SCHEMA.load(valid_payload(**{field: value}))

    assert field in error.value.messages


def test_should_reject_negative_initial_concentration():
    """KSAMPLE-N02"""
    with pytest.raises(ValidationError) as error:
        KINETICS_SAMPLE_SCHEMA.load(valid_payload(initial_concentration=-1))

    assert "initial_concentration" in error.value.messages


def test_should_reject_concentration_at_minus_one():
    """KSAMPLE-B01: -1 is the first rejected value"""
    with pytest.raises(ValidationError):
        KINETICS_SAMPLE_SCHEMA.load(valid_payload(concentration=[50, 40, -1, 25, 22]))


def test_should_zero_concentration_just_above_minus_one():
    """KSAMPLE-B02: values in (-1, 0) are instrument noise"""
    sample = KINETICS_SAMPLE_SCHEMA.load(valid_payload(concentration=[50, 40, -0.99, 25, 22]))

    assert sample.concentration == [50, 40, 0, 25, 22]


@pytest.mark.parametrize("field", ["time", "qt", "concentration"])
@pytest.mark.parametrize("value", [[0, None, 10, 20, 30], "abc", 5])
def test_should_reject_null_items_and_non_lists_without_raising_type_error(field, value):
    """KSAMPLE-N03: must be a ValidationError (400), never a TypeError (500)"""
    with pytest.raises(ValidationError):
        KINETICS_SAMPLE_SCHEMA.load(valid_payload(**{field: value}))
