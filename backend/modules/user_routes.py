from flask import Blueprint, request, jsonify
from extensions import db, bcrypt
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy.orm import joinedload
from modules.models import User, Company
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

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(name=company_name)
        db.session.add(company)
        db.session.commit()

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=hashed_password, company_id=company.id)
    db.session.add(new_user)
    db.session.commit()

    logging.info(f"New user registered: {username}")
    return jsonify({'message': 'User registered successfully'}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(
            identity=user.username,  # 'identity' must be a string
            additional_claims={'company': user.company.name}
        )
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.options(joinedload(User.company)).all()
    users_list = [{'username': user.username, 'email': user.email, 'company': user.company.name if user.company else None} for user in users]
    return jsonify(users_list), 200
