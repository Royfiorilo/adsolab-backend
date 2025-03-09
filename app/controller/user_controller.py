from flask import Blueprint, request, jsonify
from flask_security import auth_required, roles_required
from flask_security.utils import hash_password

from app import db, User
from start import app

blueprint = Blueprint("user", __name__)


# Helper to validate email format
def is_valid_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


@blueprint.route('/api/users', methods=['POST'])
@auth_required()
@roles_required('ADMIN')
def create_user():
    data = request.get_json()

    # Validate required fields
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    # Validate email format
    if not is_valid_email(data.get('email')):
        return jsonify({'error': 'Invalid email format'}), 400

    # Check if user already exists
    if app.security.datastore.find_user(email=data.get('email')):
        return jsonify({'error': 'User with this email already exists'}), 409

    # Get role (default to 'DEFAULT' if not specified or invalid)
    role_name = data.get('role', 'DEFAULT')
    if role_name not in ['DEFAULT', 'ADMIN']:
        role_name = 'DEFAULT'

    # Find or create the role
    role = app.security.datastore.find_or_create_role(role_name)

    # Create the user
    user = app.security.datastore.create_user(
        email=data.get('email'),
        password=hash_password(data.get('password')),
    )

    # Add role to user
    app.security.datastore.add_role_to_user(user, role)

    # Commit changes
    db.session.commit()

    return jsonify({
        'id': user.id,
        'email': user.email,
        'role': role_name,
        'active': user.active
    }), 201


@app.route('/api/users', methods=['GET'])
@auth_required()
@roles_required('ADMIN')
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Set limits to prevent excessive queries
    per_page = min(per_page, 100)

    users = User.query.paginate(page=page, per_page=per_page)

    result = []
    for user in users.items:
        user_roles = [role.name for role in user.roles]
        result.append({
            'id': user.id,
            'email': user.email,
            'roles': user_roles,
            'active': user.active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })

    return jsonify({
        'users': result,
        'page': users.page,
        'per_page': users.per_page,
        'total': users.total,
        'pages': users.pages
    })


@app.route('/api/users/<int:user_id>', methods=['GET'])
@auth_required()
def get_user(user_id):
    # Check if requesting user is either an admin or the user themselves
    current_user = app.security.current_user
    if not (current_user.id == user_id or any(role.name == 'ADMIN' for role in current_user.roles)):
        return jsonify({'error': 'Unauthorized access'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'roles': [role.name for role in user.roles],
        'active': user.active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    })


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@auth_required()
def update_user(user_id):
    # Check if requesting user is either an admin or the user themselves
    current_user = app.security.current_user
    if not (current_user.id == user_id or any(role.name == 'ADMIN' for role in current_user.roles)):
        return jsonify({'error': 'Unauthorized access'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    changes_made = False

    # Update email if provided and valid
    if 'email' in data and data['email'] != user.email:
        if not is_valid_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Check if email is already in use
        existing_user = app.security.datastore.find_user(email=data['email'])
        if existing_user and existing_user.id != user_id:
            return jsonify({'error': 'Email already in use'}), 409

        user.email = data['email']
        changes_made = True

    # Update password if provided
    if 'password' in data and data['password']:
        user.password = hash_password(data['password'])
        changes_made = True

    # Update role if admin and role provided
    if 'role' in data and any(role.name == 'ADMIN' for role in current_user.roles):
        if data['role'] not in ['DEFAULT', 'ADMIN']:
            return jsonify({'error': 'Invalid role'}), 400

        # Remove all existing roles
        for role in user.roles:
            app.security.datastore.remove_role_from_user(user, role)

        # Add the new role
        role = app.security.datastore.find_or_create_role(data['role'])
        app.security.datastore.add_role_to_user(user, role)
        changes_made = True

    # Update active status if admin and status provided
    if 'active' in data and any(role.name == 'ADMIN' for role in current_user.roles):
        if not isinstance(data['active'], bool):
            return jsonify({'error': 'Active status must be a boolean'}), 400

        user.active = data['active']
        changes_made = True

    # Save changes if any were made
    if changes_made:
        db.session.commit()

    return jsonify({
        'id': user.id,
        'email': user.email,
        'roles': [role.name for role in user.roles],
        'active': user.active,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    })


# Delete a user
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@auth_required()
@roles_required('ADMIN')
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Don't allow deleting the current user
    current_user = app.security.current_user
    if current_user.id == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': f'User {user_id} deleted successfully'})
