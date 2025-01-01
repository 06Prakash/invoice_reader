# backend/modules/user_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from modules.services.user_service import create_user, get_all_users, authenticate_user, search_user_service
from modules.middleware.admin_middleware import special_admin_required

from modules.logging_util import setup_logger

logger = setup_logger()

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

    logger.info(f"New user registered: {username}")
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

@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_user():
    """
    Search for a user by username or email.
    """
    query = request.args.get('query', '').strip()
    logger.info(f"Query collected: {query}")

    # Use the service to perform the search
    result = search_user_service(query)
    logger.info(f"Result Obtained: {result}")

    # If the result is a dictionary with an 'error' key, return an error response
    if 'error' in result:
        logger.error(f"Error: {result['error']}")
        return jsonify(result), 400 if result['error'] == 'Search query is required' else 404

    # Otherwise, return the user data
    logger.info(f"User Found: {result}")
    return jsonify(result), 200



@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users_list = get_all_users()
    return jsonify(users_list), 200