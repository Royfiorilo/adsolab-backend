"""ABE-002: invalid or degenerate kinetics requests end in explicit errors, not 500."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from entities.kinetics_sample import KineticsSampleEntity
from exceptions.exceptions import BadRequestError, LinearizationError, NotFoundError
from services import user_service
from services.kinetics_investigation_service import MAX_PER_PAGE, get_kinetic_investigations
from services.kinetics_linearization_service import _run_single_linearization, _solve_params
from services.kinetics_no_linear_model_service import MIN_FIT_POINTS, run_kinetic_no_linear_models
from services.kinetics_version_service import validate_kinetic_version_payload

PSO_EQUATIONS = {"m": "1/qe", "b": "1/(k2 * qe**2)"}
PSO_LINEARIZATION = {
    "name": "PSO", "linearization_id": 5,
    "parameters": {"x": "time", "y": "time/qt", **PSO_EQUATIONS},
}


def sample_with(points):
    return KineticsSampleEntity(time=[float(i) for i in range(points)], qt=[float(i) for i in range(points)])


def run_fit_request(points, **extra):
    request = {"kinetic_sample_id": 1, "models": [{"model": 3, "seeds": []}], **extra}
    with patch('app.db'),             patch('services.kinetics_sample_service.find_kinetic_sample', return_value=sample_with(points)),             patch('services.kinetics_no_linear_model_service.find_kinetic_model') as find_model:
        try:
            return run_kinetic_no_linear_models(request)
        finally:
            lookups.append(find_model.call_count)


lookups = []


@pytest.mark.parametrize("points", [2, 3, MIN_FIT_POINTS - 1])
def test_should_reject_fit_when_sample_has_fewer_points_than_the_minimum(points):
    """KFIT-N01"""
    lookups.clear()

    with pytest.raises(BadRequestError) as error:
        run_fit_request(points)

    assert str(MIN_FIT_POINTS) in error.value.message
    assert lookups == [0]  # no model was loaded, so nothing was fitted


def test_should_count_points_after_the_filter():
    """KFIT-N02: 6 points minus 2 filtered leaves 4"""
    with pytest.raises(BadRequestError):
        run_fit_request(MIN_FIT_POINTS + 1, filter=[0, 1])


def version_result(**overrides):
    result = {"model": 1, "best_adjust": "leastsq", "adjustment_methods": [{"name": "leastsq"}]}
    result.update(overrides)
    return result


COMPARISON = {"heuristic": {"best_model": 1, "results": []}}


@pytest.mark.parametrize("field", ["model", "best_adjust", "adjustment_methods"])
def test_should_reject_version_when_a_required_field_is_null(field):
    """KSAVE-N01: best_adjust null used to pass and break a NOT NULL column"""
    with pytest.raises(BadRequestError) as error:
        validate_kinetic_version_payload([version_result(**{field: None})], COMPARISON)

    assert field in error.value.message


def test_should_reject_version_when_a_result_is_not_an_object():
    """KSAVE-N02"""
    with pytest.raises(BadRequestError):
        validate_kinetic_version_payload(["leastsq"], COMPARISON)


def test_should_accept_version_when_all_required_fields_are_present():
    """KSAVE-H01"""
    validate_kinetic_version_payload([version_result()], COMPARISON)


@pytest.mark.parametrize("page, per_page", [(0, 20), (-1, 20), (1, 0), (1, -5)])
def test_should_reject_listing_with_page_or_per_page_below_one(page, per_page):
    """KLIST-N01"""
    with pytest.raises(BadRequestError):
        get_kinetic_investigations(page, per_page)


def test_should_cap_per_page_at_the_maximum():
    """KLIST-B01"""
    with patch('services.kinetics_investigation_service.db') as db:
        query = db.session.query.return_value
        query.count.return_value = 0

        result = get_kinetic_investigations(1, MAX_PER_PAGE + 1)

    query.offset.return_value.limit.assert_called_once_with(MAX_PER_PAGE)
    assert result["per_page"] == MAX_PER_PAGE


def line(slope, intercept):
    return SimpleNamespace(slope=slope, intercept=intercept, stderr=0.1, intercept_stderr=0.1)


def test_should_raise_when_the_equations_have_no_solution():
    """KLIN-N01: PSO with a zero slope means 1/qe = 0, which has no solution"""
    with pytest.raises(LinearizationError):
        _solve_params(PSO_EQUATIONS, line(slope=0.0, intercept=1.0))


def test_should_solve_pso_parameters_when_the_line_is_valid():
    """KLIN-H01: slope 1/qe = 0.2 gives qe = 5 and k2 = 1/(b * qe**2) = 0.04"""
    values, _ = _solve_params(PSO_EQUATIONS, line(slope=0.2, intercept=1.0))

    assert values["qe"] == pytest.approx(5.0, rel=1e-9)
    assert values["k2"] == pytest.approx(0.04, rel=1e-9)


def test_should_report_error_status_instead_of_ok_with_empty_parameters():
    """KLIN-N02: qt proportional to time makes time/qt constant, so the fitted slope is 0"""
    flat = KineticsSampleEntity(time=[1.0, 2.0, 3.0, 4.0], qt=[2.0, 4.0, 6.0, 8.0])

    result = _run_single_linearization(flat, PSO_LINEARIZATION)

    assert result["status"] == "ERROR"
    assert result["reason"]


def test_should_return_not_found_when_deleting_a_missing_user():
    """KUSER-N01: used to be 400"""
    with patch.object(user_service, 'User') as user_model:
        user_model.query.get.return_value = None

        with pytest.raises(NotFoundError):
            user_service.delete_user(99)
