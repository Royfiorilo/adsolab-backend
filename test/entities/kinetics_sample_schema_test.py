import unittest

from marshmallow import ValidationError

from entities.kinetics_sample import KineticsSampleEntity
from entities.schemas.kinetics_sample_schema import KINETICS_SAMPLE_SCHEMA


def build_payload(**overrides):
    payload = {
        "time": [0, 5, 10, 20, 30],
        "qt": [0, 3.2, 5.1, 6.8, 7.4],
        "temperature": 298,
        "time_unit": "min",
        "measure_unit": "mg/g",
        "adsorbate_id": 1,
        "adsorbent_id": 2,
    }
    payload.update(overrides)
    return payload


class TestKineticsSampleSchema(unittest.TestCase):
    def test_should_load_entity_when_time_and_qt_are_valid(self):
        sample = KINETICS_SAMPLE_SCHEMA.load(build_payload())

        self.assertIsInstance(sample, KineticsSampleEntity)
        self.assertEqual(sample.time, [0.0, 5.0, 10.0, 20.0, 30.0])
        self.assertEqual(sample.qt, [0.0, 3.2, 5.1, 6.8, 7.4])
        self.assertEqual(sample.adsorbate_id, 1)
        self.assertEqual(sample.adsorbent_id, 2)

    def test_should_reject_sample_without_qt_and_without_concentration(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(build_payload(qt=None))

    def test_should_reject_sample_when_time_and_qt_have_different_lengths(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(build_payload(qt=[0, 3.2, 5.1]))

    def test_should_reject_sample_with_negative_qt(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(build_payload(qt=[0, 3.2, -5.1, 6.8, 7.4]))

    def test_should_reject_sample_with_negative_time(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(build_payload(time=[-2, 5, 10, 20, 30]))

    def test_should_reject_sample_with_less_than_two_points(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(build_payload(time=[0], qt=[0]))

    def test_should_reject_sample_without_adsorbate_id(self):
        payload = build_payload()
        del payload["adsorbate_id"]
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(payload)

    def test_should_reject_concentration_without_conversion_parameters(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(
                build_payload(qt=None, concentration=[50, 40, 33, 27, 24])
            )

    def test_should_load_concentration_when_conversion_parameters_are_present(self):
        sample = KINETICS_SAMPLE_SCHEMA.load(
            build_payload(
                qt=None,
                concentration=[50, 40, 33, 27, 24],
                initial_concentration=50,
                volume=0.25,
                adsorbent_mass=0.5,
            )
        )

        self.assertIsNone(sample.qt)
        self.assertEqual(sample.concentration, [50.0, 40.0, 33.0, 27.0, 24.0])
        self.assertEqual(sample.initial_concentration, 50.0)

    def test_should_reject_concentration_with_different_length_than_time(self):
        with self.assertRaises(ValidationError):
            KINETICS_SAMPLE_SCHEMA.load(
                build_payload(
                    qt=None,
                    concentration=[50, 40],
                    initial_concentration=50,
                    volume=0.25,
                    adsorbent_mass=0.5,
                )
            )

    def test_should_normalize_small_negative_values_to_zero(self):
        sample = KINETICS_SAMPLE_SCHEMA.load(
            build_payload(qt=[-0.004, 3.2, 5.1, 6.8, 7.4])
        )

        self.assertEqual(sample.qt[0], 0.0)


if __name__ == "__main__":
    unittest.main()
