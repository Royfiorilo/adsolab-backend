"""ABE-003: reading, listing and saving around soft-deleted kinetic samples, on PostgreSQL."""
import pytest

from database import KineticInvestigation, KineticVersion
from exceptions.exceptions import NotFoundError
from services.kinetics_investigation_service import validate_and_save_kinetic_version
from services.kinetics_sample_service import (
    delete_kinetic_sample,
    find_kinetic_sample,
    find_readable_kinetic_sample,
    get_all_kinetic_samples,
)
from services.kinetics_version_service import delete_kinetic_version, get_kinetic_versions

pytestmark = pytest.mark.integration

ADJUSTMENT_METHODS = [{"name": "leastsq", "success": True, "parameters": [], "statistics": {}}]
HEURISTIC = {"best_model": 2, "results": [{"model": 2, "score": 1.0}]}


def save_version(sample, investigation_id=None):
    request = {
        "kinetic_sample_id": sample.kinetic_sample_id,
        "results": [{"model": 2, "best_adjust": "leastsq", "adjustment_methods": ADJUSTMENT_METHODS}],
        "comparison": {"heuristic": HEURISTIC},
    }
    if investigation_id is not None:
        request["kinetic_investigation_id"] = investigation_id
    return validate_and_save_kinetic_version(request, sample.user_id)


def delete(sample):
    delete_kinetic_sample(sample.kinetic_sample_id, sample.user_id)


def count(session, model, **filters):
    return session.query(model).filter_by(**filters).count()


# ---------------------------------------------------------------------------
# Reading a sample by id
# ---------------------------------------------------------------------------

def test_should_read_an_active_sample_with_no_deleted_at(db_session, make_kinetic_sample):
    """KDEL-H01"""
    sample = make_kinetic_sample()

    read = find_readable_kinetic_sample(sample.kinetic_sample_id)

    assert read.deleted_at is None


def test_should_read_a_deleted_sample_while_it_has_saved_versions(db_session, make_kinetic_sample):
    """KDEL-H02"""
    sample = make_kinetic_sample()
    save_version(sample)
    delete(sample)

    read = find_readable_kinetic_sample(sample.kinetic_sample_id)

    assert read.kinetic_sample_id == sample.kinetic_sample_id
    assert read.deleted_at is not None


def test_should_not_read_a_deleted_sample_that_has_no_versions(db_session, make_kinetic_sample):
    """KDEL-N01"""
    sample = make_kinetic_sample()
    delete(sample)

    with pytest.raises(NotFoundError):
        find_readable_kinetic_sample(sample.kinetic_sample_id)


def test_should_not_read_a_deleted_sample_after_its_last_version_is_deleted(db_session, make_kinetic_sample):
    """KDEL-S01: with two versions the sample stays readable until the second one goes"""
    sample = make_kinetic_sample()
    first = save_version(sample)
    second = save_version(sample, first["kinetic_investigation_id"])
    delete(sample)
    investigation_id = first["kinetic_investigation_id"]

    delete_kinetic_version(investigation_id, first["version_id"], sample.user_id)
    still_readable = find_readable_kinetic_sample(sample.kinetic_sample_id)
    delete_kinetic_version(investigation_id, second["version_id"], sample.user_id)

    assert still_readable.deleted_at is not None
    with pytest.raises(NotFoundError):
        find_readable_kinetic_sample(sample.kinetic_sample_id)


def test_should_not_read_a_sample_that_never_existed(db_session):
    """KDEL-N02"""
    with pytest.raises(NotFoundError):
        find_readable_kinetic_sample(2_000_000_000)


# ---------------------------------------------------------------------------
# What a deleted sample keeps and what it rejects
# ---------------------------------------------------------------------------

def test_should_keep_investigation_and_versions_when_the_sample_is_deleted(db_session, make_kinetic_sample):
    """KDEL-H03"""
    sample = make_kinetic_sample()
    saved = save_version(sample)
    investigation_id = saved["kinetic_investigation_id"]

    delete(sample)
    db_session.expire_all()

    assert count(db_session, KineticInvestigation, kinetic_investigation_id=investigation_id) == 1
    assert count(db_session, KineticVersion, kinetic_investigation_id=investigation_id) == 1
    assert [v.version_id for v in get_kinetic_versions(investigation_id)] == [1]


def test_should_reject_a_deleted_sample_for_new_analyses_even_with_versions(db_session, make_kinetic_sample):
    """KDEL-N03: linearization, seeds and fit load the sample with find_kinetic_sample"""
    sample = make_kinetic_sample()
    save_version(sample)
    delete(sample)

    with pytest.raises(NotFoundError):
        find_kinetic_sample(sample.kinetic_sample_id)


def test_should_reject_saving_a_version_for_a_deleted_sample(db_session, make_kinetic_sample):
    """KDEL-N04: no investigation id"""
    sample = make_kinetic_sample()
    delete(sample)

    with pytest.raises(NotFoundError):
        save_version(sample)

    assert count(db_session, KineticInvestigation, kinetic_sample_id=sample.kinetic_sample_id) == 0


def test_should_reject_saving_with_an_existing_investigation_after_the_sample_is_deleted(
        db_session, make_kinetic_sample):
    """KDEL-N05: used to save a second version on a deleted sample"""
    sample = make_kinetic_sample()
    first = save_version(sample)
    delete(sample)

    with pytest.raises(NotFoundError):
        save_version(sample, first["kinetic_investigation_id"])

    assert count(db_session, KineticVersion, kinetic_investigation_id=first["kinetic_investigation_id"]) == 1


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------

def listed_ids(**kwargs):
    return {sample.kinetic_sample_id for sample in get_all_kinetic_samples(**kwargs)}


def test_should_list_only_active_samples(db_session, make_kinetic_sample):
    """KLIST-H01"""
    kept = make_kinetic_sample()
    removed = make_kinetic_sample()
    save_version(removed)
    delete(removed)

    ids = listed_ids()

    assert kept.kinetic_sample_id in ids
    assert removed.kinetic_sample_id not in ids


def test_should_list_only_the_samples_of_the_requested_user(db_session, make_user, make_kinetic_sample):
    """KLIST-H02"""
    owner = make_user()
    other = make_user()
    mine = [make_kinetic_sample(user_id=owner.id), make_kinetic_sample(user_id=owner.id)]
    theirs = make_kinetic_sample(user_id=other.id)

    ids = listed_ids(user_id=owner.id)

    assert ids == {sample.kinetic_sample_id for sample in mine}
    assert theirs.kinetic_sample_id not in ids


def test_should_raise_not_found_when_the_user_has_no_samples(db_session, make_user):
    """KLIST-E01: the existing empty-list behavior is kept"""
    user = make_user()

    with pytest.raises(NotFoundError):
        get_all_kinetic_samples(user_id=user.id)
