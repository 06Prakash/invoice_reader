from decimal import Decimal
from extensions import db
from modules.models.personal_credit import PersonalCredit
from modules.models.business_credit import BusinessCredit
from modules.models.user import User
from modules.models.company import Company
from modules.logging_util import setup_logger

logger = setup_logger()

def update_credit(entity_id, credit_count):
    """
    Update the credit count for a user or a company.

    :param entity_id: The ID of the user or company whose credits need to be updated.
    :param credit_count: The new credit count to set (Decimal).
    :return: A success or error response.
    """
    logger.info("Entered into the update credit function")
    credit_count = Decimal(credit_count)

    # Determine if the entity is a user
    user = User.query.get(entity_id)
    if user:
        # If the user belongs to a company, update business credits
        if user.company_id:
            company = Company.query.get(user.company_id)
            if not company:
                return {'error': f'Company with ID {user.company_id} not found'}, 404
            
            # Update or create BusinessCredit
            credit = BusinessCredit.query.filter_by(company_id=company.id).first()
            if not credit:
                credit = BusinessCredit(company_id=company.id, credit_count=credit_count)
                db.session.add(credit)
            else:
                credit.credit_count = credit_count

            db.session.commit()
            return {
                'message': f'BusinessCredits updated successfully for company {company.name}',
                'current_credits': float(credit.credit_count)
            }
        else:
            # Update or create PersonalCredit for the user
            credit = PersonalCredit.query.filter_by(user_id=entity_id).first()
            if not credit:
                credit = PersonalCredit(user_id=entity_id, credit_count=credit_count)
                db.session.add(credit)
            else:
                credit.credit_count = credit_count

            db.session.commit()
            return {
                'message': f'PersonalCredits updated successfully for user {user.username}',
                'current_credits': float(credit.credit_count)
            }

    # If no user is found, check if it's a company directly
    company = Company.query.get(entity_id)
    if company:
        # Update or create BusinessCredit for the company
        credit = BusinessCredit.query.filter_by(company_id=entity_id).first()
        if not credit:
            credit = BusinessCredit(company_id=entity_id, credit_count=credit_count)
            db.session.add(credit)
        else:
            credit.credit_count = credit_count

        db.session.commit()
        return {
            'message': f'BusinessCredits updated successfully for company {company.name}',
            'current_credits': float(credit.credit_count)
        }

    # If neither user nor company is found
    return {'error': 'Entity not found'}, 404

def get_remaining_credits(user_id):
    """
    Fetch the remaining credits for a user or their associated company.

    :param user_id: ID of the user
    :return: Total remaining credits as Decimal
    """
    user = User.query.get(user_id)
    if not user:
        return Decimal(0)  # User not found

    if user.company_id:
        # If the user is associated with a company, fetch business credits
        credit_entry = BusinessCredit.query.filter_by(company_id=user.company_id).first()
        if credit_entry:
            return credit_entry.credit_count
    else:
        # If the user is a personal user, fetch user-specific credits
        credit_entry = PersonalCredit.query.filter_by(user_id=user_id).first()
        if credit_entry:
            return credit_entry.credit_count

    return Decimal(0)  # No credits found for the user or company

def update_business_credits(company_id, credit_increment):
    company = Company.query.get(company_id)
    if not company:
        return {'error': 'Company not found'}, 404

    # Check if business credit already exists
    business_credit = BusinessCredit.query.filter_by(company_id=company.id).first()
    if not business_credit:
        business_credit = BusinessCredit(company_id=company.id, credit_count=Decimal(0))
        db.session.add(business_credit)

    # Update credit count
    business_credit.credit_count += Decimal(credit_increment)
    db.session.commit()

    return {
        'message': 'Business credits updated successfully',
        'current_credits': float(business_credit.credit_count)
    }

def validate_credits(user_id, pages_to_process):
    """
    Validates if the user has enough credits to process the given number of pages.

    :param user_id: ID of the user.
    :param pages_to_process: Number of pages to process.
    :raises ValueError: If sufficient credits are not available.
    """
    user = User.query.get(user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise ValueError("User not found")

    required_credits = Decimal(pages_to_process)

    # Check for company or personal credits
    if user.company_id:
        business_credit = BusinessCredit.query.filter_by(company_id=user.company_id).first()
        available_credits = business_credit.credit_count if business_credit else Decimal(0)
    else:
        personal_credit = PersonalCredit.query.filter_by(user_id=user.id).first()
        available_credits = personal_credit.credit_count if personal_credit else Decimal(0)

    if available_credits < required_credits:
        logger.error(
            f"Insufficient credits for user {user.username}. Required: {required_credits}, "
            f"Available: {available_credits}"
        )
        raise ValueError("Insufficient credits available. Please purchase more credits.")

def reduce_credits(user_id, pages_to_process):
    """
    Deducts credits after successful processing.

    :param user_id: ID of the user.
    :param pages_to_process: Number of pages processed.
    """
    user = User.query.get(user_id)
    deduction_amount = Decimal(pages_to_process)

    if user.company_id:
        # Deduct from business credits
        business_credit = BusinessCredit.query.filter_by(company_id=user.company_id).first()
        if business_credit:
            business_credit.credit_count -= deduction_amount
            logger.info(
                f"Deducted {deduction_amount} business credits for company ID {user.company_id}. "
                f"Remaining: {business_credit.credit_count}"
            )
    else:
        # Deduct from personal credits
        personal_credit = PersonalCredit.query.filter_by(user_id=user.id).first()
        if personal_credit:
            personal_credit.credit_count -= deduction_amount
            logger.info(
                f"Deducted {deduction_amount} personal credits for user {user.username}. "
                f"Remaining: {personal_credit.credit_count}"
            )

    db.session.commit()
