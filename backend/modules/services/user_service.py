# backend/modules/services/user_service.py
from extensions import db, bcrypt
from modules.models.user import User
from modules.models.company import Company
from modules.models.credit import Credit
from modules.logging_util import setup_logger
from sqlalchemy.orm import joinedload
from flask_jwt_extended import get_jwt_identity

logger = setup_logger()

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

def reduce_credits_for_user(user_id, total_pages):
    """
    Validates and deducts credits from the specified user's account based on the total pages processed.

    :param user_id: ID of the user whose credits will be deducted.
    :param total_pages: Number of pages processed for extraction.
    :raises ValueError: If the user does not have sufficient credits or the user is not found.
    """
    user = User.query.get(user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise ValueError("User not found")

    if not user.credits or user.credits[0].credit_count < total_pages:
        logger.error(
            f"Insufficient credits for user {user.username}. Required: {total_pages}, "
            f"Available: {user.credits[0].credit_count if user.credits else 0}"
        )
        raise ValueError("Insufficient credits... Please purchase credits and retry.")

    # Deduct credits
    user.credits[0].credit_count -= total_pages
    db.session.commit()
    logger.info(
        f"Deducted {total_pages} credits from user {user.username}. "
        f"Remaining credits: {user.credits[0].credit_count}"
    )


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

def search_user_service(query):
    """
    Search for a user by username or email.
    """
    logger.info(f"Service Query: {query}")

    if not query:
        return {'error': 'Search query is required'}, 400

    user = User.query.options(joinedload(User.credits)).filter(
        (User.username.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).first()

    if not user:
        logger.info("User not found in database.")
        return {'error': 'User not found'}, 404

    total_credits = sum(credit.credit_count for credit in user.credits)
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'credit_count': total_credits,
        'is_special_admin': user.special_admin
    }
