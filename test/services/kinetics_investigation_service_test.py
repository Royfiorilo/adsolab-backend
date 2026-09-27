import unittest
from unittest.mock import MagicMock, patch

from exceptions.exceptions import BadRequestError, ForbiddenError, NotFoundError
from services.kinetics_investigation_service import (
    create_kinetic_investigation,
    validate_and_save_kinetic_version,
)

SAMPLE_ID = 3
OWNER_ID = 7
NEW_INVESTIGATION_ID = 11


def valid_request(**overrides):
    request = {
        "kinetic_sample_id": SAMPLE_ID,
        "results": [{"model": 1, "best_adjust": "leastsq", "adjustment_methods": [], "seeds": []}],
        "comparison": {"heuristic": {"best_model": 1, "results": []}, "ml": None},
    }
    request.update(overrides)
    return request


class TestCreateKineticInvestigation(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_investigation_service.db")
        self.sample_patcher = patch("services.kinetics_investigation_service.find_kinetic_sample")
        self.session = self.db_patcher.start().session
        self.find_sample = self.sample_patcher.start()

    def tearDown(self):
        self.db_patcher.stop()
        self.sample_patcher.stop()

    def test_should_flush_without_committing_a_new_investigation(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        create_kinetic_investigation(SAMPLE_ID, OWNER_ID)

        self.session.add.assert_called_once()
        self.session.flush.assert_called_once()
        self.session.commit.assert_not_called()

    def test_should_reuse_the_investigation_of_the_same_sample_and_user(self):
        existing = MagicMock()
        self.session.query.return_value.filter_by.return_value.first.return_value = existing

        investigation = create_kinetic_investigation(SAMPLE_ID, OWNER_ID)

        self.assertIs(investigation, existing)
        self.session.add.assert_not_called()

    def test_should_raise_not_found_and_create_nothing_when_sample_does_not_exist(self):
        self.find_sample.side_effect = NotFoundError("no sample")

        with self.assertRaises(NotFoundError):
            create_kinetic_investigation(SAMPLE_ID, OWNER_ID)

        self.session.add.assert_not_called()


class TestValidateAndSaveKineticVersion(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_investigation_service.db")
        self.create_patcher = patch("services.kinetics_investigation_service.create_kinetic_investigation")
        self.save_patcher = patch("services.kinetics_investigation_service.save_kinetic_version")
        self.session = self.db_patcher.start().session
        self.create_investigation = self.create_patcher.start()
        self.save_version = self.save_patcher.start()
        self.create_investigation.return_value = MagicMock(kinetic_investigation_id=NEW_INVESTIGATION_ID)
        self.save_version.return_value = MagicMock(version_id=1)

    def tearDown(self):
        self.db_patcher.stop()
        self.create_patcher.stop()
        self.save_patcher.stop()

    def test_should_not_create_an_investigation_when_results_are_invalid(self):
        with self.assertRaises(BadRequestError):
            validate_and_save_kinetic_version(valid_request(results=[]), OWNER_ID)

        self.create_investigation.assert_not_called()
        self.save_version.assert_not_called()

    def test_should_not_create_an_investigation_when_comparison_has_no_heuristic(self):
        with self.assertRaises(BadRequestError):
            validate_and_save_kinetic_version(valid_request(comparison={"ml": None}), OWNER_ID)

        self.create_investigation.assert_not_called()

    def test_should_save_the_version_into_the_new_investigation(self):
        response = validate_and_save_kinetic_version(valid_request(), OWNER_ID)

        self.create_investigation.assert_called_once_with(SAMPLE_ID, OWNER_ID)
        self.assertEqual(self.save_version.call_args.kwargs["kinetic_investigation_id"], NEW_INVESTIGATION_ID)
        self.assertEqual(response, {"status": "ok", "kinetic_investigation_id": NEW_INVESTIGATION_ID, "version_id": 1})

    def test_should_raise_forbidden_when_saving_into_another_user_investigation(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = MagicMock(user_id=999)

        with self.assertRaises(ForbiddenError):
            validate_and_save_kinetic_version(valid_request(kinetic_investigation_id=5), OWNER_ID)

        self.save_version.assert_not_called()

    def test_should_raise_not_found_when_the_given_investigation_does_not_exist(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            validate_and_save_kinetic_version(valid_request(kinetic_investigation_id=5), OWNER_ID)


if __name__ == "__main__":
    unittest.main()
