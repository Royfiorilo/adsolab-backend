import unittest

from marshmallow import ValidationError

from app.entities.sample import SampleEntity  # Importa la entidad si es necesaria para las pruebas
from app.entities.schemas.sample_schema import SAMPLE_SCHEMA


class SchemaSchemaTest(unittest.TestCase):

    def setUp(self):
        self.valid_sample_data = {
            "ce": [1.0, 2.0, 3.0],
            "qe": [4.0, 5.0, 6.0]
        }

    def test_valid_sample(self):
        result = SAMPLE_SCHEMA.load(self.valid_sample_data)
        self.assertIsInstance(result, SampleEntity)
        self.assertEqual(result.ce, [1.0, 2.0, 3.0])
        self.assertEqual(result.qe, [4.0, 5.0, 6.0])

    def test_sample_schema_ce_normalization_invalid(self):
        invalid_data = {
            "ce": [1.5, -6.5, 2.0],
            "qe": [1.0, 2.0, 3.0],

        }

        self.assertRaises(ValidationError, SAMPLE_SCHEMA.load, invalid_data)

    def test_sample_schema_qe_normalization_invalid(self):
        invalid_data = {
            "ce": [1.5, 9.5, 2.0],
            "qe": [1.0, 2.0, -3.0],

        }

        self.assertRaises(ValidationError, SAMPLE_SCHEMA.load, invalid_data)

    def test_sample_schema_ce_normalization_allowed(self):
        invalid_data = {
            "ce": [1.5, -0.5, 2.0],
            "qe": [1.0, 2.0, 3.0],

        }

        sample = SAMPLE_SCHEMA.load(invalid_data)
        self.assertEqual(sample.ce[1], 0)

    def test_ce_qe_length_mismatch(self):
        data = {
            "ce": [1.0, 2.0],
            "qe": [3.0, 4.0, 5.0]
        }
        self.assertRaises(ValidationError, SAMPLE_SCHEMA.load, data)

    def test_missing_required_field(self):
        data = {
            "ce": [1.0, 2.0, 3.0]
        }
        with self.assertRaises(ValidationError):
            SAMPLE_SCHEMA.load(data)

    def test_empty_list(self):
        data = {
            "ce": [],
            "qe": [1.0]
        }
        with self.assertRaises(ValidationError):
            SAMPLE_SCHEMA.load(data)

    def test_without_investigations(self):
        result = SAMPLE_SCHEMA.load(self.valid_sample_data)
        self.assertEqual(result.investigations, [])

    def test_sample_id_dump_only(self):
        load_data = {
            "ce": [1.0],
            "qe": [2.0]
        }
        result = SAMPLE_SCHEMA.load(load_data)
        self.assertIsNone(result.id)

        sample_with_id = SampleEntity(ce=[1.0], qe=[2.0], sample_id=123)
        dumped = SAMPLE_SCHEMA.dump(sample_with_id)

        self.assertIn('sample_id', dumped)
        self.assertEqual(dumped['sample_id'], 123)

if __name__ == '__main__':
    unittest.main()
