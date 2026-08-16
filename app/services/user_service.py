from abc import ABC, abstractmethod
from flask_security.utils import hash_password

import app
from database import db, User, Role
from exceptions.exceptions import UsernameAlreadyTakenError, NotFoundError, BadRequestError, ForbiddenError

ADMIN_ROLE = 'ADMIN'
RESEARCHER_ROLE = 'RESEARCHER'
DEV_ROLE = 'DEV'


# Patrón Chain of Responsibility para actualización de usuarios
class UserUpdateHandler(ABC):
    def __init__(self):
        self._next_handler = None

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, user, data, current_user, has_permission):
        if self._next_handler:
            self._next_handler.handle(user, data, current_user, has_permission)


class EmailUpdateHandler(UserUpdateHandler):
    def handle(self, user, data, current_user, has_permission):
        if 'email' in data:
            email = data['email']
            if email != user.email:
                existing_user = app.user_datastore.find_user(email=email)
                if existing_user and existing_user.id != user.id:
                    raise UsernameAlreadyTakenError(f'The username {email} is already taken.')
                user.email = email
        super().handle(user, data, current_user, has_permission)


class PasswordUpdateHandler(UserUpdateHandler):
    def handle(self, user, data, current_user, has_permission):
        if 'password' in data and data['password']:
            if has_permission or current_user.id == user.id:
                user.password = hash_password(data['password'])
        super().handle(user, data, current_user, has_permission)


class RoleUpdateHandler(UserUpdateHandler):
    def handle(self, user, data, current_user, has_permission):
        if 'role' in data:
            if has_permission and current_user.id != user.id:
                if data['role'] not in [RESEARCHER_ROLE, ADMIN_ROLE]:
                    raise BadRequestError(f"The role {data['role']} is not supported.")
                
                for role in user.roles:
                    app.user_datastore.remove_role_from_user(user, role)
                role_obj = app.user_datastore.find_or_create_role(data['role'])
                app.user_datastore.add_role_to_user(user, role_obj)
        super().handle(user, data, current_user, has_permission)


class ActiveStatusUpdateHandler(UserUpdateHandler):
    def handle(self, user, data, current_user, has_permission):
        if 'active' in data:
            if has_permission and current_user.id != user.id:
                if not isinstance(data['active'], bool):
                    raise BadRequestError('Active status must be a boolean')
                user.active = data['active']
        super().handle(user, data, current_user, has_permission)


def create_user(email, password, role, current_user):
    user = app.user_datastore.find_user(email=email)
    
    #Patrón State
    if user and not user.is_deleted():
        raise UsernameAlreadyTakenError(f'The username {email} is already taken.')

    role_name = role or RESEARCHER_ROLE
    if role_name not in [RESEARCHER_ROLE, ADMIN_ROLE, DEV_ROLE]:
        role_name = RESEARCHER_ROLE

    # Patrón State
    if user and user.is_deleted():
        user = reactivate_user(email)
        data = {
            "email" : email,
            "password" : password,
            "role": role_name,
            "active": True
        }
        user_updated = update_user(user.id, data, current_user)
        return user_updated

    role_obj = app.user_datastore.find_or_create_role(role_name)
    user = app.user_datastore.create_user(
        email=email,
        password=hash_password(password),
    )
    app.user_datastore.add_role_to_user(user, role_obj)
    db.session.commit()

    return {
        'id': user.id,
        'email': user.email,
        'role': role_name,
        'active': user.active
    }


def get_users(page, per_page):
    per_page = min(per_page, 100)
    users = User.query.filter(~User.roles.any(Role.name == "DEV"), User.deleted_at == None).paginate(page=page, per_page=per_page)

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
    user = User.query.filter(~User.roles.any(Role.name == "DEV"),
                             User.deleted_at == None,
                             User.id == user_id).first()
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

    allowed_roles = {ADMIN_ROLE, DEV_ROLE}
    has_permission = any(role.name in allowed_roles for role in current_user.roles)

    if user_id != current_user.id and not has_permission:
        raise ForbiddenError(f'User {current_user.id} is not authorized to edit this user.')

    if current_user.id == user_id and ('active' in data or 'role' in data):
        raise ForbiddenError(f'Current user can not modify role and active status')

    # Orquestación de la cadena de responsabilidad
    email_handler = EmailUpdateHandler()
    password_handler = PasswordUpdateHandler()
    role_handler = RoleUpdateHandler()
    active_handler = ActiveStatusUpdateHandler()

    email_handler.set_next(password_handler).set_next(role_handler).set_next(active_handler)

    # Ejecución de la cadena
    email_handler.handle(user, data, current_user, has_permission)

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

    # Patrón State
    user.soft_delete()
    db.session.commit()

    return {'message': f'User {user_id} deleted successfully'}


def reactivate_user(email):
    user = app.user_datastore.find_user(email=email)
    if not user:
        raise BadRequestError('User not found.')
    
    # Patrón State
    user.reactivate()
    db.session.commit()
    return user