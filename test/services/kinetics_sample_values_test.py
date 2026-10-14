"""ABE-001: sorting and qt computation of kinetic samples."""
import pytest
from marshmallow import ValidationError

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_sample_service import prepare_sample_values


def sample(**overrides):
    values = {
        "time": [0.0, 5.0, 10.0],
        "qt": None,
        "concentration": [50.0, 40.0, 30.0],
        "initial_concentration": 50.0,
        "volume": 0.25,
        "adsorbent_mass": 0.5,
    }
    values.update(overrides)
    return KineticsSampleEntity(**values)


def test_should_keep_time_qt_and_concentration_aligned_when_input_is_unsorted():
    """KSAMPLE-S01: the concentration at index i must belong to the time at index i"""
    unsorted = sample(time=[10.0, 0.0, 5.0], concentration=[30.0, 50.0, 40.0])

    time, qt, concentration = prepare_sample_values(unsorted)

    assert time == [0.0, 5.0, 10.0]
    assert concentration == [50.0, 40.0, 30.0]
    assert qt == [0.0, 5.0, 10.0]  # (C0 - Ct) * V / m is exact for these binary-friendly values


def test_should_sort_concentration_with_the_same_permutation_when_qt_is_sent():
    """KSAMPLE-S02: ties on time are ordered by qt, concentration follows"""
    unsorted = sample(time=[5.0, 5.0, 0.0], qt=[4.0, 3.0, 0.0], concentration=[42.0, 44.0, 50.0])

    time, qt, concentration = prepare_sample_values(unsorted)

    assert (time, qt, concentration) == ([0.0, 5.0, 5.0], [0.0, 3.0, 4.0], [50.0, 44.0, 42.0])


def test_should_return_none_concentration_when_it_was_not_sent():
    """KSAMPLE-E01"""
    time, qt, concentration = prepare_sample_values(
        sample(time=[5.0, 0.0], qt=[3.0, 0.0], concentration=None)
    )

    assert (time, qt, concentration) == ([0.0, 5.0], [0.0, 3.0], None)


def test_should_store_zero_when_computed_qt_is_instrument_noise():
    """KSAMPLE-B03: Ct slightly above C0 gives qt in (-1, 0)"""
    noisy = sample(concentration=[50.0, 50.5, 30.0])  # qt = -0.25 for the second point

    _, qt, _ = prepare_sample_values(noisy)

    assert qt[1] == 0


def test_should_reject_when_computed_qt_is_minus_one_or_lower():
    """KSAMPLE-B04: qt = (50 - 52) * 0.25 / 0.5 = -1.0, the first rejected value"""
    with pytest.raises(ValidationError):
        prepare_sample_values(sample(concentration=[50.0, 52.0, 30.0]))
