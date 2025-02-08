# backend/modules/services/user_service.py
from extensions import db, bcrypt
from modules.models.user import User
from modules.models.company import Company
from modules.models.personal_credit import PersonalCredit
from modules.models.business_credit import BusinessCredit
from modules.logging_util import setup_logger
from sqlalchemy.orm import joinedload
from flask_jwt_extended import get_jwt_identity

logger = setup_logger(__name__)

def get_user(username):
    return User.query.filter_by(username=username).first()


def create_user(username, email, password, company_id=None):
    # Check if the username or email already exists
    if User.query.filter_by(username=username).first():
        return {'error': 'Username already exists'}, 400
    if User.query.filter_by(email=email).first():
        return {'error': 'Email already exists'}, 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create a new user
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        company_id=company_id
    )
    db.session.add(new_user)
    db.session.commit()

    # Log the new user's ID
    logger.info(f"Created user with ID: {new_user.id}")
    if not new_user.id:
        logger.error("User ID was not generated. Aborting credit creation.")
        return {'error': 'Failed to create user'}, 500

    # Assign default personal credits
    default_personal_credit = PersonalCredit(user_id=new_user.id, credit_count=5)
    db.session.add(default_personal_credit)
    db.session.commit()

    return {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'credits': default_personal_credit.credit_count
    }

def reduce_credits_for_user(user_id, total_pages):
    """
    Validates and deducts credits from the user's account based on the total pages processed.
    If the user belongs to a company (has a company_id), the company's business credits are deducted.
    Otherwise, the user's personal credits are reduced.

    :param user_id: ID of the user whose credits will be deducted.
    :param total_pages: Number of pages processed for extraction.
    :raises ValueError: If sufficient credits are not available or the user/company is not found.
    """
    user = User.query.get(user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise ValueError("User not found")

    # Check if the user belongs to a company
    if user.company_id:
        # Handle business credits
        company = Company.query.get(user.company_id)
        if not company:
            logger.error(f"Company with ID {user.company_id} not found.")
            raise ValueError("Company not found")

        business_credit = BusinessCredit.query.filter_by(company_id=company.id).first()
        if not business_credit or business_credit.credit_count < total_pages:
            logger.error(
                f"Insufficient business credits for company {company.name}. "
                f"Required: {total_pages}, Available: {business_credit.credit_count if business_credit else 0}"
            )
            raise ValueError("Insufficient business credits... Please contact your administrator.")

        # Deduct business credits
        business_credit.credit_count -= total_pages
        db.session.commit()
        logger.info(
            f"Deducted {total_pages} credits from company {company.name}. "
            f"Remaining business credits: {business_credit.credit_count}"
        )
    else:
        # Handle personal credits
        personal_credit = PersonalCredit.query.filter_by(user_id=user.id).first()
        if not personal_credit or personal_credit.credit_count < total_pages:
            logger.error(
                f"Insufficient personal credits for user {user.username}. Required: {total_pages}, "
                f"Available: {personal_credit.credit_count if personal_credit else 0}"
            )
            raise ValueError("Insufficient personal credits... Please purchase credits and retry.")

        # Deduct personal credits
        personal_credit.credit_count -= total_pages
        db.session.commit()
        logger.info(
            f"Deducted {total_pages} credits from user {user.username}. "
            f"Remaining personal credits: {personal_credit.credit_count}"
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
    Search for a user by username or email and calculate their total credits.

    :param query: The search query (username or email).
    :return: A dictionary with user details and total credits.
    """
    logger.info(f"Service Query: {query}")

    if not query:
        return {'error': 'Search query is required'}

    # Search for the user by username or email
    user = User.query.options(joinedload(User.company)).filter(
        (User.username.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
    ).first()

    if not user:
        logger.info("User not found in database.")
        return {'error': 'User not found'}

    # Calculate total credits
    total_credits = 0

    # If the user belongs to a company, use business credits
    if user.company_id:
        business_credit_entry = BusinessCredit.query.filter_by(company_id=user.company_id).first()
        total_credits = business_credit_entry.credit_count if business_credit_entry else 0
    else:
        # Otherwise, use personal credits
        personal_credit_entry = PersonalCredit.query.filter_by(user_id=user.id).first()
        total_credits = personal_credit_entry.credit_count if personal_credit_entry else 0

    # Return user details with total credits
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'credit_count': total_credits,
        'company': user.company.name if user.company else None,
        'company_id': user.company.id if user.company else None,
        'is_special_admin': user.special_admin
    }

def is_email_registered(email):
    """
    Check if the email exists in the database.

    :param email: The email to check.
    :return: True if the email exists, False otherwise.
    """
    user = get_user_by_email(email)
    return user is not None

def get_user_by_email(email):
    """
    Retrieve a user by their email address.

    :param email: The email of the user.
    :return: The User object if found, otherwise None.
    """
    return User.query.filter_by(email=email).first()

