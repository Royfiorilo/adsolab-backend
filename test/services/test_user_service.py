import unittest
from unittest.mock import MagicMock, patch

import app
from app import Role, User, db
from services.user_service import create_user, ADMIN_ROLE


class TestUserService(unittest.TestCase):

    @patch('flask_security.utils.hash_password')
    def test_create_user(self, mock_hash_password):
        app.user_datastore.find_user = MagicMock(return_value=None)
        app.user_datastore.find_or_create_role = MagicMock(return_value=Role(name=ADMIN_ROLE))
        mock_hash_password = '<PASSWORD>'
        app.user_datastore.create_user = MagicMock(return_value=User(email='<EMAIL>'))
        app.user_datastore.add_role_to_user = MagicMock()
        db.session.commit = MagicMock()

        result = create_user("test@example.com", "password123", ADMIN_ROLE)

        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
