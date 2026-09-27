import unittest

from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError

from database import KineticComparison, KineticVersion

HEURISTIC = {"best_model": 1, "results": []}


class TestKineticComparisonUniqueness(unittest.TestCase):
    """`version_id` is numbered per investigation, so only the pair must be unique."""

    def setUp(self):
        # Only the two tables under test; SQLite does not enforce the FKs to the rest.
        self.engine = create_engine("sqlite://")
        KineticVersion.__table__.create(self.engine)
        KineticComparison.__table__.create(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def save_version(self, investigation_id, version_id):
        with self.engine.begin() as connection:
            connection.execute(insert(KineticVersion.__table__).values(
                kinetic_investigation_id=investigation_id, version_id=version_id,
            ))
            connection.execute(insert(KineticComparison.__table__).values(
                kinetic_investigation_id=investigation_id, version_id=version_id, heuristic=HEURISTIC,
            ))

    def test_should_allow_version_one_in_several_investigations(self):
        self.save_version(investigation_id=1, version_id=1)
        self.save_version(investigation_id=2, version_id=1)

    def test_should_allow_several_versions_of_one_investigation(self):
        self.save_version(investigation_id=1, version_id=1)
        self.save_version(investigation_id=1, version_id=2)

    def test_should_reject_a_second_comparison_for_the_same_version(self):
        self.save_version(investigation_id=1, version_id=1)

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(insert(KineticComparison.__table__).values(
                    kinetic_investigation_id=1, version_id=1, heuristic=HEURISTIC,
                ))


if __name__ == "__main__":
    unittest.main()
