# backend/modules/user_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from modules.services.user_service import create_user, get_all_users, authenticate_user
from modules.middleware.admin_middleware import special_admin_required

import logging

logging.basicConfig(level=logging.INFO)

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    company_name = data.get('company', '').strip()

    if not username or not email or not password or not company_name:
        return jsonify({'message': 'All fields are required'}), 400

    result = create_user(username, email, password, company_name)
    if isinstance(result, dict) and 'error' in result:
        return jsonify({'message': result['error']}), 400

    logging.info(f"New user registered: {username}")
    return jsonify({'message': 'User registered successfully'}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login, generating an access token and returning user details.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Authenticate the user
    user = authenticate_user(username, password)
    if user:
        # Create a JWT token with additional claims
        access_token = create_access_token(
            identity=str(user.id),  # Convert user ID to string explicitly
            additional_claims={
                'special_admin': user.special_admin,  # Add special_admin status to the token
                'company': user.company.name if user.company else None  # Add company name if available
            }
        )
        return jsonify({
            'access_token': access_token,
            'special_admin': user.special_admin,  # Include special_admin in the response
            'username': user.username  # Include username for personalization
        }), 200

    return jsonify({'message': 'Invalid credentials'}), 401


@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users_list = get_all_users()
    return jsonify(users_list), 200

@user_bp.route('/user/search', methods=['GET'])
@jwt_required()
def search_user():
    """
    Search for a user by username or email.
    """
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    user = User.query.filter(
        (User.username.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'credit_count': sum(credit.credit_count for credit in user.credits),
        'is_special_admin': user.special_admin
    }), 200