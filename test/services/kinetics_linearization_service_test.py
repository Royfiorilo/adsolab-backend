import math
import unittest
from unittest.mock import MagicMock, patch

from entities.formula import Formula
from entities.kinetics_sample import KineticsSampleEntity
from exceptions.exceptions import LinearizationError
from services.kinetics_linearization_service import (
    _resolve_known_params,
    _run_single_linearization,
    _transform_points,
    run_kinetic_linearization,
)

QE, K1, K2, KID, C = 7.5, 0.15, 0.02, 1.2, 0.5
TIMES = [0.0, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0]

INTRAPARTICLE_LIN = {
    "linearization_id": 1,
    "name": "Linealización Intraparticular",
    "parameters": {"x": "time**0.5", "y": "qt", "m": "kid", "b": "C"},
}
PSO_LIN = {
    "linearization_id": 2,
    "name": "Linealización Pseudo-Segundo Orden",
    "parameters": {"x": "time", "y": "time/qt", "m": "1/qe", "b": "1/(k2 * qe**2)"},
}
PFO_LIN = {
    "linearization_id": 3,
    "name": "Linealización PFO (Lagergren)",
    "parameters": {"x": "time", "y": "ln(qe - qt)", "m": "-k1", "b": "ln(qe)"},
}


def intraparticle_sample(times=TIMES):
    return KineticsSampleEntity(
        time=list(times), qt=[KID * math.sqrt(t) + C for t in times]
    )


def pso_sample(times=TIMES):
    return KineticsSampleEntity(
        time=list(times), qt=[(K2 * QE ** 2 * t) / (1 + K2 * QE * t) for t in times]
    )


def pfo_sample(times=TIMES):
    return KineticsSampleEntity(
        time=list(times), qt=[QE * (1 - math.exp(-K1 * t)) for t in times]
    )


def params_by_name(result):
    return {p["name"]: p["value"] for p in result["parameters"]}


class TestResolveKnownParams(unittest.TestCase):
    def test_should_return_empty_when_formulas_only_use_measured_variables(self):
        known = _resolve_known_params(
            intraparticle_sample(), Formula("time**0.5"), Formula("qt"), None
        )

        self.assertEqual(known, {})

    def test_should_estimate_qe_as_max_qt_when_not_provided(self):
        sample = pfo_sample()

        known = _resolve_known_params(
            sample, Formula("time"), Formula("ln(qe - qt)"), None
        )

        self.assertEqual(known, {"qe": max(sample.qt)})

    def test_should_prefer_provided_value_over_estimator(self):
        known = _resolve_known_params(
            pfo_sample(), Formula("time"), Formula("ln(qe - qt)"), {"qe": 9.9}
        )

        self.assertEqual(known, {"qe": 9.9})

    def test_should_raise_when_parameter_has_no_estimator(self):
        with self.assertRaises(LinearizationError):
            _resolve_known_params(
                pfo_sample(), Formula("time"), Formula("qt / k0"), None
            )


class TestTransformPoints(unittest.TestCase):
    def test_should_keep_every_point_when_all_are_transformable(self):
        sample = intraparticle_sample()

        x_dots, y_dots, dropped = _transform_points(
            sample, Formula("time**0.5"), Formula("qt"), {}
        )

        self.assertEqual(len(x_dots), len(TIMES))
        self.assertEqual(len(y_dots), len(TIMES))
        self.assertEqual(dropped, 0)
        self.assertEqual(x_dots[1], round(math.sqrt(5.0), 4))

    def test_should_drop_initial_point_when_time_is_zero_in_pso(self):
        sample = pso_sample()

        x_dots, _, dropped = _transform_points(
            sample, Formula("time"), Formula("time/qt"), {}
        )

        self.assertEqual(dropped, 1)
        self.assertEqual(len(x_dots), len(TIMES) - 1)
        self.assertNotIn(0.0, x_dots)

    def test_should_use_injected_qe_and_drop_non_finite_point_in_pfo(self):
        sample = pfo_sample()
        qe_estimated = max(sample.qt)

        x_dots, y_dots, dropped = _transform_points(
            sample, Formula("time"), Formula("ln(qe - qt)"), {"qe": qe_estimated}
        )

        self.assertEqual(dropped, 1)
        self.assertEqual(len(x_dots), len(TIMES) - 1)
        self.assertTrue(all(math.isfinite(y) for y in y_dots))

    def test_should_raise_when_fewer_than_two_points_are_transformable(self):
        sample = KineticsSampleEntity(time=[0.0, 1.0], qt=[0.0, 0.0])

        with self.assertRaises(LinearizationError):
            _transform_points(sample, Formula("time"), Formula("time/qt"), {})


class TestRunSingleLinearization(unittest.TestCase):
    def test_should_recover_intraparticle_parameters_from_synthetic_data(self):
        result = _run_single_linearization(intraparticle_sample(), INTRAPARTICLE_LIN)

        self.assertEqual(result["status"], "OK")
        self.assertAlmostEqual(result["statistics"]["r_squared"], 1.0, places=4)
        self.assertAlmostEqual(params_by_name(result)["kid"], KID, places=3)
        self.assertAlmostEqual(params_by_name(result)["C"], C, places=3)
        self.assertEqual(result["dropped_points"], 0)

    def test_should_recover_pso_parameters_ignoring_the_zero_time_point(self):
        result = _run_single_linearization(pso_sample(), PSO_LIN)

        self.assertEqual(result["status"], "OK")
        self.assertAlmostEqual(result["statistics"]["r_squared"], 1.0, places=4)
        self.assertAlmostEqual(params_by_name(result)["qe"], QE, places=3)
        self.assertAlmostEqual(params_by_name(result)["k2"], K2, places=4)
        self.assertEqual(result["dropped_points"], 1)

    def test_should_recover_pfo_parameters_when_qe_is_provided(self):
        result = _run_single_linearization(pfo_sample(), PFO_LIN, {"qe": QE})

        self.assertEqual(result["status"], "OK")
        self.assertAlmostEqual(params_by_name(result)["k1"], K1, places=3)
        self.assertEqual(result["assumed_params"], {"qe": QE})

    def test_should_report_estimated_qe_when_not_provided_for_pfo(self):
        sample = pfo_sample()

        result = _run_single_linearization(sample, PFO_LIN)

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["assumed_params"], {"qe": max(sample.qt)})
        self.assertAlmostEqual(params_by_name(result)["k1"], K1, places=2)

    def test_should_return_error_status_instead_of_raising_on_degenerate_sample(self):
        sample = KineticsSampleEntity(time=[0.0, 1.0], qt=[0.0, 0.0])

        result = _run_single_linearization(sample, PSO_LIN)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["id"], PSO_LIN["linearization_id"])
        self.assertIn("reason", result)

    def test_should_return_error_status_when_linearization_lacks_axis_formulas(self):
        result = _run_single_linearization(
            pso_sample(), {"linearization_id": 9, "name": "rota", "parameters": {}}
        )

        self.assertEqual(result["status"], "ERROR")


class TestRunKineticLinearization(unittest.TestCase):
    def run_service(self, sample, lin_data_list, model_request=None):
        model_request = model_request or {"model": 1, "linearizations": [1, 2]}
        schema = MagicMock()
        schema.dump.side_effect = lin_data_list

        with patch('app.db'), \
                patch('services.kinetics_sample_service.find_kinetic_sample', return_value=sample), \
                patch('entities.schemas.kinetics_model_schema.KINETICS_LINEARIZATION_SCHEMA', schema):
            return run_kinetic_linearization({
                "kinetic_sample_id": 1,
                "models": [model_request],
            })

    def test_should_pick_the_linearization_with_the_highest_r_squared_as_best(self):
        results = self.run_service(
            intraparticle_sample(), [INTRAPARTICLE_LIN, PSO_LIN]
        )

        by_id = {r["id"]: r for r in results[0]["linearizations"]}
        self.assertEqual(len(by_id), 2)
        self.assertGreater(
            by_id[INTRAPARTICLE_LIN["linearization_id"]]["statistics"]["r_squared"],
            by_id[PSO_LIN["linearization_id"]]["statistics"]["r_squared"],
        )
        self.assertEqual(results[0]["best_result"], INTRAPARTICLE_LIN["linearization_id"])

    def test_should_not_pick_a_failed_linearization_as_best(self):
        broken = {
            "linearization_id": 8,
            "name": "sin estimador",
            "parameters": {"x": "time", "y": "qt / k0", "m": "k0", "b": "C"},
        }

        results = self.run_service(intraparticle_sample(), [broken, INTRAPARTICLE_LIN])

        statuses = {r["id"]: r["status"] for r in results[0]["linearizations"]}
        self.assertEqual(statuses[broken["linearization_id"]], "ERROR")
        self.assertEqual(results[0]["best_result"], INTRAPARTICLE_LIN["linearization_id"])

    def test_should_forward_known_params_from_the_request(self):
        results = self.run_service(
            pfo_sample(),
            [PFO_LIN],
            {"model": 3, "linearizations": [3], "known_params": {"qe": 9.9}},
        )

        self.assertEqual(results[0]["linearizations"][0]["assumed_params"], {"qe": 9.9})


if __name__ == "__main__":
    unittest.main()
