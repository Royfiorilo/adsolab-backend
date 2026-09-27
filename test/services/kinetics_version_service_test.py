import unittest
from unittest.mock import MagicMock, patch

from exceptions.exceptions import BadRequestError, ForbiddenError, NotFoundError
from services.kinetics_version_service import (
    delete_kinetic_version,
    get_kinetic_version,
    get_kinetic_versions,
    save_kinetic_version,
)

INVESTIGATION_ID = 1
OWNER_ID = 7


def mock_investigation(user_id=OWNER_ID):
    investigation = MagicMock()
    investigation.kinetic_investigation_id = INVESTIGATION_ID
    investigation.user_id = user_id
    return investigation


def valid_results():
    return [{
        "model": 1,
        "best_adjust": "leastsq",
        "seeds": [{"name": "kid", "value": 1.0}],
        "adjustment_methods": [{
            "name": "leastsq",
            "success": True,
            "parameters": [{"name": "kid", "value": 0.82, "std_err": 0.01}],
            "statistics": {"r_squared": 0.99},
            "residuals": {"values": [0.01, -0.01], "analysis": {}},
            "transformed": {"x": [0, 1], "y": [0, 1]},
        }],
    }]


def valid_comparison():
    return {"heuristic": {"best_model": 1, "results": [{"model": 1, "score": 0.9}]}, "ml": None}


class TestSaveKineticVersion(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_version_service.db")
        self.mock_db = self.db_patcher.start()
        self.session = self.mock_db.session

    def tearDown(self):
        self.db_patcher.stop()

    def test_should_raise_not_found_when_investigation_does_not_exist(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            save_kinetic_version(INVESTIGATION_ID, valid_results(), valid_comparison())

    def test_should_raise_bad_request_when_results_are_empty(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = mock_investigation()

        with self.assertRaises(BadRequestError):
            save_kinetic_version(INVESTIGATION_ID, [], valid_comparison())

    def test_should_raise_bad_request_when_result_is_missing_required_fields(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = mock_investigation()
        broken_results = [{"model": 1, "best_adjust": "leastsq"}]

        with self.assertRaises(BadRequestError):
            save_kinetic_version(INVESTIGATION_ID, broken_results, valid_comparison())

    def test_should_raise_bad_request_when_comparison_has_no_heuristic(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = mock_investigation()

        with self.assertRaises(BadRequestError):
            save_kinetic_version(INVESTIGATION_ID, valid_results(), {"ml": None})

    def test_should_assign_version_one_when_investigation_has_no_versions(self):
        investigation_query, last_version_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, last_version_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        last_version_query.filter_by.return_value.order_by.return_value.first.return_value = None

        with patch("services.kinetics_version_service.current_app", MagicMock()):
            version = save_kinetic_version(INVESTIGATION_ID, valid_results(), valid_comparison())

        self.assertEqual(version.version_id, 1)
        self.assertEqual(self.session.add.call_count, 2)
        self.session.add_all.assert_called_once()
        self.session.commit.assert_called_once()

    def test_should_increment_version_id_from_the_last_saved_version(self):
        investigation_query, last_version_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, last_version_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        previous_version = MagicMock(version_id=3)
        last_version_query.filter_by.return_value.order_by.return_value.first.return_value = previous_version

        with patch("services.kinetics_version_service.current_app", MagicMock()):
            version = save_kinetic_version(INVESTIGATION_ID, valid_results(), valid_comparison())

        self.assertEqual(version.version_id, 4)

    def test_should_rollback_and_reraise_when_commit_fails(self):
        investigation_query, last_version_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, last_version_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        last_version_query.filter_by.return_value.order_by.return_value.first.return_value = None
        self.session.commit.side_effect = RuntimeError("db exploded")

        with self.assertRaises(RuntimeError):
            save_kinetic_version(INVESTIGATION_ID, valid_results(), valid_comparison())

        self.session.rollback.assert_called_once()


class TestGetKineticVersion(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_version_service.db")
        self.mock_db = self.db_patcher.start()
        self.session = self.mock_db.session

    def tearDown(self):
        self.db_patcher.stop()

    def test_should_return_version_row_when_it_exists(self):
        version = MagicMock(version_id=2)
        self.session.query.return_value.filter_by.return_value.first.return_value = version

        result = get_kinetic_version(INVESTIGATION_ID, 2)

        self.assertIs(result, version)

    def test_should_raise_not_found_when_version_does_not_exist(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            get_kinetic_version(INVESTIGATION_ID, 99)


class TestGetKineticVersions(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_version_service.db")
        self.mock_db = self.db_patcher.start()
        self.session = self.mock_db.session

    def tearDown(self):
        self.db_patcher.stop()

    def test_should_raise_not_found_when_investigation_does_not_exist(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            get_kinetic_versions(INVESTIGATION_ID)

    def test_should_return_versions_ordered_for_existing_investigation(self):
        investigation_query, versions_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, versions_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        versions = [MagicMock(version_id=1), MagicMock(version_id=2)]
        versions_query.filter_by.return_value.order_by.return_value.all.return_value = versions

        result = get_kinetic_versions(INVESTIGATION_ID)

        self.assertEqual(result, versions)


class TestDeleteKineticVersion(unittest.TestCase):
    def setUp(self):
        self.db_patcher = patch("services.kinetics_version_service.db")
        self.mock_db = self.db_patcher.start()
        self.session = self.mock_db.session

    def tearDown(self):
        self.db_patcher.stop()

    def test_should_raise_not_found_when_investigation_does_not_exist(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            delete_kinetic_version(INVESTIGATION_ID, 1, OWNER_ID)

    def test_should_raise_forbidden_when_user_is_not_the_owner(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = mock_investigation(
            user_id=OWNER_ID
        )

        with self.assertRaises(ForbiddenError):
            delete_kinetic_version(INVESTIGATION_ID, 1, user_id=999)

    def test_should_raise_not_found_when_version_does_not_exist(self):
        investigation_query, version_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, version_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        version_query.filter_by.return_value.first.return_value = None

        with self.assertRaises(NotFoundError):
            delete_kinetic_version(INVESTIGATION_ID, 1, OWNER_ID)

    def test_should_delete_and_commit_when_owner_and_version_are_valid(self):
        investigation_query, version_query = MagicMock(), MagicMock()
        self.session.query.side_effect = [investigation_query, version_query]
        investigation_query.filter_by.return_value.first.return_value = mock_investigation()
        version = MagicMock(version_id=1)
        version_query.filter_by.return_value.first.return_value = version

        with patch("services.kinetics_version_service.current_app", MagicMock()):
            delete_kinetic_version(INVESTIGATION_ID, 1, OWNER_ID)

        self.session.delete.assert_called_once_with(version)
        self.session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
