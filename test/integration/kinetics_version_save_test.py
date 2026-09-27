"""Save / read / delete kinetic versions on PostgreSQL. Cases: docs/test-specs/kinetics-version-save.md."""
from datetime import datetime

import pytest
from sqlalchemy.exc import DBAPIError

from database import KineticComparison, KineticFittedModel, KineticInvestigation, KineticVersion
from exceptions.exceptions import BadRequestError, ForbiddenError, NotFoundError
from services.kinetics_investigation_service import (
    delete_kinetic_investigation,
    validate_and_save_kinetic_version,
)
from services.kinetics_version_service import (
    delete_kinetic_version,
    get_kinetic_version,
    get_kinetic_versions,
)

pytestmark = pytest.mark.integration

ADJUSTMENT_METHODS = [{
    "name": "leastsq",
    "success": True,
    "parameters": [{"name": "qe", "value": 6.52, "std_err": 0.11}, {"name": "k2", "value": 0.021, "std_err": 0.002}],
    "statistics": {"r_squared": 0.9971, "RMSE": 0.12},
    "residuals": {"values": [0.0, 0.3, -0.1], "analysis": {"durbin_watson": 1.5}},
    "transformed": {"x": [0, 1, 2], "y": [0, 1.5, 2.9]},
}]
SEEDS = [{"name": "qe", "value": 6.4, "stderr": 0.2}, {"name": "k2", "value": 0.02, "stderr": None}]
HEURISTIC = {"best_model": 2, "results": [{"model": 2, "score": 1.0}]}
ML = {"best_model": 2, "results": [{"model": 2, "coef": 0.98}], "statistics": {"r_squared": 0.99}}


def payload(sample, **overrides):
    request = {
        "kinetic_sample_id": sample.kinetic_sample_id,
        "results": [{"model": 2, "best_adjust": "leastsq", "adjustment_methods": ADJUSTMENT_METHODS, "seeds": SEEDS}],
        "comparison": {"heuristic": HEURISTIC, "ml": ML},
    }
    request.update(overrides)
    return request


def payload_results():
    return [{"model": 2, "best_adjust": "leastsq", "adjustment_methods": ADJUSTMENT_METHODS}]


def count(session, model, **filters):
    return session.query(model).filter_by(**filters).count()


def investigations_of(session, sample):
    return count(session, KineticInvestigation, kinetic_sample_id=sample.kinetic_sample_id)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def test_should_create_investigation_and_first_version_when_sample_has_none(db_session, make_kinetic_sample):
    """KSAVE-H01 / KSAVE-B01"""
    sample = make_kinetic_sample()

    response = validate_and_save_kinetic_version(payload(sample), sample.user_id)

    investigation_id = response["kinetic_investigation_id"]
    assert response["version_id"] == 1
    assert investigations_of(db_session, sample) == 1
    assert count(db_session, KineticFittedModel, kinetic_investigation_id=investigation_id, version_id=1) == 1
    assert count(db_session, KineticComparison, kinetic_investigation_id=investigation_id, version_id=1) == 1


def test_should_read_back_exactly_what_was_saved(db_session, make_kinetic_sample):
    """KSAVE-H02"""
    sample = make_kinetic_sample()
    response = validate_and_save_kinetic_version(payload(sample), sample.user_id)
    db_session.expire_all()

    version = get_kinetic_version(response["kinetic_investigation_id"], response["version_id"])

    fitted_model = version.fitted_models[0]
    assert fitted_model.kinetic_model_id == 2
    assert fitted_model.adjustment_methods == ADJUSTMENT_METHODS
    assert fitted_model.seeds == SEEDS
    assert version.comparison.heuristic == HEURISTIC
    assert version.comparison.ml == ML


def test_should_reject_and_write_nothing_when_heuristic_is_an_empty_dict(db_session, make_kinetic_sample):
    """KSAVE-B02"""
    sample = make_kinetic_sample()

    with pytest.raises(BadRequestError):
        validate_and_save_kinetic_version(payload(sample, comparison={"heuristic": {}, "ml": None}), sample.user_id)

    assert investigations_of(db_session, sample) == 0


def test_should_raise_not_found_and_write_nothing_when_sample_does_not_exist(db_session, make_user):
    """KSAVE-N04"""
    user = make_user()
    before = count(db_session, KineticInvestigation)

    with pytest.raises(NotFoundError):
        validate_and_save_kinetic_version(
            {"kinetic_sample_id": 999_999, "results": payload_results(), "comparison": {"heuristic": HEURISTIC}},
            user.id,
        )

    assert count(db_session, KineticInvestigation) == before


def test_should_raise_not_found_when_sample_is_soft_deleted(db_session, make_kinetic_sample):
    """KSAVE-N05"""
    sample = make_kinetic_sample(deleted_at=datetime.utcnow())

    with pytest.raises(NotFoundError):
        validate_and_save_kinetic_version(payload(sample), sample.user_id)

    assert investigations_of(db_session, sample) == 0


def test_should_forbid_saving_into_another_user_investigation(db_session, make_kinetic_sample, make_user):
    """KSAVE-N06"""
    sample = make_kinetic_sample()
    owner_save = validate_and_save_kinetic_version(payload(sample), sample.user_id)
    intruder = make_user()
    investigation_id = owner_save["kinetic_investigation_id"]

    with pytest.raises(ForbiddenError):
        validate_and_save_kinetic_version(payload(sample, kinetic_investigation_id=investigation_id), intruder.id)

    assert count(db_session, KineticVersion, kinetic_investigation_id=investigation_id) == 1


def test_should_store_null_ml_when_comparison_has_no_ml(db_session, make_kinetic_sample):
    """KSAVE-E01"""
    sample = make_kinetic_sample()

    response = validate_and_save_kinetic_version(payload(sample, comparison={"heuristic": HEURISTIC}), sample.user_id)

    assert get_kinetic_version(response["kinetic_investigation_id"], 1).comparison.ml is None


def test_should_store_empty_seeds_when_result_has_none(db_session, make_kinetic_sample):
    """KSAVE-E02"""
    sample = make_kinetic_sample()
    results = [{"model": 2, "best_adjust": "leastsq", "adjustment_methods": ADJUSTMENT_METHODS}]

    response = validate_and_save_kinetic_version(payload(sample, results=results), sample.user_id)

    assert get_kinetic_version(response["kinetic_investigation_id"], 1).fitted_models[0].seeds == []


@pytest.mark.parametrize("given, expected", [
    ({"iterations": 500, "steps": 0.5}, (500, 0.5)),
    ({}, (None, None)),
])
def test_should_store_iterations_and_steps_as_given(db_session, make_kinetic_sample, given, expected):
    """KSAVE-E03"""
    sample = make_kinetic_sample()

    response = validate_and_save_kinetic_version(payload(sample, **given), sample.user_id)

    version = get_kinetic_version(response["kinetic_investigation_id"], 1)
    assert (version.iterations, version.steps) == expected


def test_should_add_version_two_to_the_same_investigation_on_second_save(db_session, make_kinetic_sample):
    """KSAVE-S01"""
    sample = make_kinetic_sample()
    first = validate_and_save_kinetic_version(payload(sample), sample.user_id)

    second = validate_and_save_kinetic_version(payload(sample), sample.user_id)

    assert second == {**first, "version_id": 2}
    assert investigations_of(db_session, sample) == 1


def test_should_create_no_investigation_when_payload_is_invalid(db_session, make_kinetic_sample):
    """KSAVE-S02"""
    sample = make_kinetic_sample()

    with pytest.raises(BadRequestError):
        validate_and_save_kinetic_version(payload(sample, results=[]), sample.user_id)

    assert investigations_of(db_session, sample) == 0


def test_should_let_each_investigation_have_its_own_version_one(db_session, make_kinetic_sample):
    """KSAVE-S03 (regression: per-column UNIQUE)"""
    first_sample, second_sample = make_kinetic_sample(), make_kinetic_sample()

    first = validate_and_save_kinetic_version(payload(first_sample), first_sample.user_id)
    second = validate_and_save_kinetic_version(payload(second_sample), second_sample.user_id)

    assert first["version_id"] == second["version_id"] == 1
    assert first["kinetic_investigation_id"] != second["kinetic_investigation_id"]


def test_should_roll_back_the_new_investigation_when_writing_the_version_fails(db_session, make_kinetic_sample):
    """KSAVE-S04 (non-numeric model fails at commit)"""
    sample = make_kinetic_sample()
    broken = [{"model": "no-es-un-id", "best_adjust": "leastsq", "adjustment_methods": ADJUSTMENT_METHODS}]

    with pytest.raises(DBAPIError):
        validate_and_save_kinetic_version(payload(sample, results=broken), sample.user_id)

    assert investigations_of(db_session, sample) == 0


def test_should_add_next_version_when_saving_into_own_investigation_explicitly(db_session, make_kinetic_sample):
    """KSAVE-S05"""
    sample = make_kinetic_sample()
    investigation_id = validate_and_save_kinetic_version(payload(sample), sample.user_id)["kinetic_investigation_id"]

    response = validate_and_save_kinetic_version(
        payload(sample, kinetic_investigation_id=investigation_id), sample.user_id
    )

    assert response == {"status": "ok", "kinetic_investigation_id": investigation_id, "version_id": 2}


# ---------------------------------------------------------------------------
# Read, list, delete
# ---------------------------------------------------------------------------

def save_versions(sample, amount):
    responses = [validate_and_save_kinetic_version(payload(sample), sample.user_id) for _ in range(amount)]
    return responses[0]["kinetic_investigation_id"]


def test_should_list_versions_in_ascending_order(db_session, make_kinetic_sample):
    """KSAVE-H04"""
    sample = make_kinetic_sample()
    investigation_id = save_versions(sample, 3)

    versions = get_kinetic_versions(investigation_id)

    assert [version.version_id for version in versions] == [1, 2, 3]


def test_should_forbid_deleting_a_version_of_another_user(db_session, make_kinetic_sample, make_user):
    """KSAVE-N12"""
    sample = make_kinetic_sample()
    investigation_id = save_versions(sample, 1)
    intruder = make_user()

    with pytest.raises(ForbiddenError):
        delete_kinetic_version(investigation_id, 1, intruder.id)

    assert count(db_session, KineticVersion, kinetic_investigation_id=investigation_id) == 1


def test_should_delete_a_version_with_its_fitted_models_and_comparison_only(db_session, make_kinetic_sample):
    """KSAVE-S07"""
    sample = make_kinetic_sample()
    investigation_id = save_versions(sample, 2)

    delete_kinetic_version(investigation_id, 1, sample.user_id)

    remaining = {"kinetic_investigation_id": investigation_id}
    assert count(db_session, KineticFittedModel, version_id=1, **remaining) == 0
    assert count(db_session, KineticComparison, version_id=1, **remaining) == 0
    assert count(db_session, KineticVersion, version_id=2, **remaining) == 1
    assert count(db_session, KineticFittedModel, version_id=2, **remaining) == 1


def test_should_delete_every_version_when_deleting_the_investigation(db_session, make_kinetic_sample):
    """KSAVE-S08"""
    sample = make_kinetic_sample()
    investigation_id = save_versions(sample, 2)

    delete_kinetic_investigation(investigation_id, sample.user_id)

    for model in (KineticVersion, KineticFittedModel, KineticComparison):
        assert count(db_session, model, kinetic_investigation_id=investigation_id) == 0
