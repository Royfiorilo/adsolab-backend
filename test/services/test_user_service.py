import unittest
from unittest.mock import MagicMock, patch

from services.user_service import create_user

import pytest
from unittest.mock import MagicMock, patch
from exceptions.exceptions import UsernameAlreadyTakenError, NotFoundError, BadRequestError

# Constants to match your service
ADMIN_ROLE = 'ADMIN'
RESEARCHER_ROLE = 'RESEARCHER'



# Test cases
def test_create_user_success(mock_app, mock_db, mock_hash_password):
    mock_app.user_datastore.find_user.return_value = None

    mock_role = MagicMock()
    mock_role.name = RESEARCHER_ROLE
    mock_app.user_datastore.find_or_create_role.return_value = mock_role

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = 'test@example.com'
    mock_user.active = True
    mock_app.user_datastore.create_user.return_value = mock_user


    # Execute
    result = create_user('test@example.com', 'password123', RESEARCHER_ROLE)

    # Assert
    mock_app.user_datastore.find_user.assert_called_once_with(email='test@example.com')
    mock_app.user_datastore.find_or_create_role.assert_called_once_with(RESEARCHER_ROLE)
    mock_app.user_datastore.create_user.assert_called_once_with(
        email='test@example.com',
        password='hashed_password'
    )
    mock_app.user_datastore.add_role_to_user.assert_called_once_with(mock_user, mock_role)
    mock_db.session.commit.assert_called_once()

    assert result == {
        'id': 1,
        'email': 'test@example.com',
        'role': RESEARCHER_ROLE,
        'active': True
    }


def test_create_user_already_exists(mock_app, mock_db, mock_hash_password):
    # Setup - user already exists
    mock_app.user_datastore.find_user.return_value = MagicMock()

    # Import the function under test
    from your_module import create_user

    # Execute and Assert
    with pytest.raises(UsernameAlreadyTakenError) as excinfo:
        create_user('existing@example.com', 'password123', RESEARCHER_ROLE)

    assert 'The username existing@example.com is already taken.' in str(excinfo.value)
    mock_app.user_datastore.find_user.assert_called_once_with(email='existing@example.com')
    mock_app.user_datastore.create_user.assert_not_called()


def test_create_user_default_role(mock_app, mock_db, mock_hash_password):
    # Setup
    mock_app.user_datastore.find_user.return_value = None

    mock_role = MagicMock()
    mock_role.name = RESEARCHER_ROLE
    mock_app.user_datastore.find_or_create_role.return_value = mock_role

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = 'test@example.com'
    mock_user.active = True
    mock_app.user_datastore.create_user.return_value = mock_user

    # Import the function under test
    from your_module import create_user

    # Execute - pass None for role to test default
    result = create_user('test@example.com', 'password123', None)

    # Assert
    mock_app.user_datastore.find_or_create_role.assert_called_once_with(RESEARCHER_ROLE)
    assert result['role'] == RESEARCHER_ROLE


def test_create_user_invalid_role(mock_app, mock_db, mock_hash_password):
    # Setup
    mock_app.user_datastore.find_user.return_value = None

    mock_role = MagicMock()
    mock_role.name = RESEARCHER_ROLE
    mock_app.user_datastore.find_or_create_role.return_value = mock_role

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = 'test@example.com'
    mock_user.active = True
    mock_app.user_datastore.create_user.return_value = mock_user

    # Import the function under test
    from your_module import create_user

    # Execute - pass invalid role
    result = create_user('test@example.com', 'password123', 'INVALID_ROLE')

    # Assert
    mock_app.user_datastore.find_or_create_role.assert_called_once_with(RESEARCHER_ROLE)
    assert result['role'] == RESEARCHER_ROLE

