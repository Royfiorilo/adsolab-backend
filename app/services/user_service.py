from flask_security.utils import hash_password

import app
from database import db, User
from exceptions.exceptions import UsernameAlreadyTakenError, NotFoundError, BadRequestError, ForbiddenError

ADMIN_ROLE = 'ADMIN'
RESEARCHER_ROLE = 'RESEARCHER'


def create_user(email, password, role):
    if app.user_datastore.find_user(email=email):
        raise UsernameAlreadyTakenError(f'The username {email} is already taken.')

    role_name = role or RESEARCHER_ROLE
    if role_name not in [RESEARCHER_ROLE, ADMIN_ROLE]:
        role_name = RESEARCHER_ROLE

    role = app.user_datastore.find_or_create_role(role_name)
    user = app.user_datastore.create_user(
        email=email,
        password=hash_password(password),
    )
    app.user_datastore.add_role_to_user(user, role)
    db.session.commit()

    return {
        'id': user.id,
        'email': user.email,
        'role': role_name,
        'active': user.active
    }


def get_users(page, per_page):
    per_page = min(per_page, 100)
    users = User.query.paginate(page=page, per_page=per_page)
    result = [{
        'id': user.id,
        'email': user.email,
        'roles': [role.name for role in user.roles],
        'active': user.active
    } for user in users.items]

    return {
        'users': result,
        'page': users.page,
        'per_page': users.per_page,
        'total': users.total,
        'pages': users.pages
    }


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'User {user_id} not found.')

    return {
        'id': user.id,
        'email': user.email,
        'roles': [role.name for role in user.roles],
        'active': user.active
    }


def update_user(user_id, data, current_user):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'User {user_id} not found.')

    if user_id != current_user.id and not any(role.name == ADMIN_ROLE for role in current_user.roles):
        raise ForbiddenError(f'User {current_user.id} is not authorized to edit this user.')

    email = data['email']
    if 'email' in data and email != user.email:
        existing_user = app.user_datastore.find_user(email=email)
        if existing_user and existing_user.id != user_id:
            raise UsernameAlreadyTakenError(f'The username {email} is already taken.')
        user.email = email

    if 'password' in data and data['password'] and (any(role.name == ADMIN_ROLE for role in current_user.roles) or current_user.id == user.id):
        user.password = hash_password(data['password'])


    if 'role' in data and any(role.name == ADMIN_ROLE for role in current_user.roles):
        if data['role'] not in [RESEARCHER_ROLE, ADMIN_ROLE]:
            raise BadRequestError(f'The role {data["role"]} is not supported.')

        for role in user.roles:
            app.user_datastore.remove_role_from_user(user, role)
        role = app.user_datastore.find_or_create_role(data['role'])
        app.user_datastore.add_role_to_user(user, role)

    if 'active' in data and any(role.name == ADMIN_ROLE for role in current_user.roles):
        if not isinstance(data['active'], bool):
            raise BadRequestError('Active status must be a boolean')
        user.active = data['active']

    db.session.commit()

    return {
        'id': user.id,
        'email': user.email,
        'roles': [role.name for role in user.roles],
        'active': user.active
    }


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise BadRequestError(f'User {user_id} not found.')

    db.session.delete(user)
    db.session.commit()

    return {'message': f'User {user_id} deleted successfully'}
