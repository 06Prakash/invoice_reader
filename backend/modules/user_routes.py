# backend/modules/user_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from modules.services.user_service import create_user, get_all_users, authenticate_user
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
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = authenticate_user(username, password)
    if user:
        access_token = create_access_token(
            identity=user.username,
            additional_claims={'company': user.company.name}
        )
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users_list = get_all_users()
    return jsonify(users_list), 200
