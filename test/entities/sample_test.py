import unittest

from entities.sample import SampleEntity


class TestSampleEntity(unittest.TestCase):
    def setUp(self):
        self.entity = SampleEntity(
            ce=[0.0, 0.25, 0.5, 0.75, 1.0],
            qe=[0.0, 0.2, 0.3, 0.4, 0.5],
            sample_id=1,
            title="Test Sample",
            description="test",
            temperature=280,
            measure_unit="mmol",
            adsorbate_id=1,
            adsorbent_id=1,
            deleted_at=None
        )

    def test_id_property(self):
        self.assertEqual(self.entity.id, 1)

    def test_length(self):
        self.assertEqual(len(self.entity), 5)

    def test_remove_single_index(self):
        self.entity.remove([1])
        self.assertEqual(self.entity.ce, [0.0, 0.5, 0.75, 1.0])
        self.assertEqual(self.entity.qe, [0.0, 0.3, 0.4, 0.5])

    def test_remove_multiple_indexes(self):
        self.entity.remove([0, 2])
        self.assertEqual(self.entity.ce, [0.25, 0.75, 1.0])
        self.assertEqual(self.entity.qe, [0.2, 0.4, 0.5])

    def test_remove_out_of_range_index(self):
        self.entity.remove([10])
        self.assertEqual(self.entity.ce, [0.0, 0.25, 0.5, 0.75, 1.0])
        self.assertEqual(self.entity.qe, [0.1, 0.2, 0.3, 0.4, 0.5])

    def test_remove_empty_list(self):
        self.entity.remove([])
        self.assertEqual(self.entity.ce, [0.0, 0.25, 0.5, 0.75, 1.0])
        self.assertEqual(self.entity.qe, [0.1, 0.2, 0.3, 0.4, 0.5])

if __name__ == "__main__":
    unittest.main()
