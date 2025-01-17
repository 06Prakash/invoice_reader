from extensions import db
from modules.models.company import Company
from sqlalchemy.exc import IntegrityError
from modules.logging_util import setup_logger

logger = setup_logger(__name__)

def update_company_credits(company_id, credit_increment):
    """Update credits for a company."""
    company = Company.query.get(company_id)
    if not company:
        return {'error': 'Company not found'}, 404

    company.credit_count += credit_increment
    db.session.commit()
    return {'message': 'Company credits updated successfully', 'current_credits': company.credit_count}


def create_company(name, initial_credits=0.00):
    """
    Create a new company with optional initial credits.

    Args:
        name (str): Name of the company.
        initial_credits (float): Initial credits to allocate to the company.

    Returns:
        dict: Success or error message with details.
    """
    try:
        # Check if the company already exists
        existing_company = Company.query.filter_by(name=name).first()
        logger.info(f"Adding company {name}")
        if existing_company:
            return {'error': f"Company with name '{name}' already exists."}, 400

        # Create the new company
        company = Company(name=name, is_deleted=False)
        db.session.add(company)
        db.session.flush()  # Generate the company ID before committing

        # Add initial credits if applicable
        if initial_credits > 0:
            from modules.models.business_credit import BusinessCredit  # Import here to avoid circular imports
            business_credit = BusinessCredit(
                company_id=company.id,
                credit_count=initial_credits
            )
            db.session.add(business_credit)

        db.session.commit()
        return {'message': f"Company '{name}' created successfully.", 'company_id': company.id}, 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        return {'error': f"Database integrity error: {str(e)}"}, 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred: {str(e)}")
        return {'error': f"An error occurred: {str(e)}"}, 500
