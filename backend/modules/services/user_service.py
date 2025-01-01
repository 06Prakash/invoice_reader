# backend/modules/services/user_service.py
from extensions import db, bcrypt
from modules.models.user import User
from modules.models.company import Company
from sqlalchemy.orm import joinedload
from flask_jwt_extended import create_access_token

def create_user(username, email, password, company_name):
    if User.query.filter_by(username=username).first():
        return {'error': 'Username already exists'}, 400

    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(name=company_name)
        db.session.add(company)
        db.session.commit()

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        company_id=company.id
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_all_users():
    users = User.query.options(joinedload(User.company)).all()
    return [
        {
            'username': user.username,
            'email': user.email,
            'company': user.company.name if user.company else None
        }
        for user in users
    ]


def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return user
    return None

