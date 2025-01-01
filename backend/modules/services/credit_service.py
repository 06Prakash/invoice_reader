from extensions import db
from modules.models.credit import Credit
from modules.models.user import User
from modules.models.company import Company

def update_credit(entity_id, credit_count):
    """
    Update the credit count for a user or a company.

    :param entity_id: The ID of the user or company whose credits need to be updated.
    :param credit_count: The new credit count to set.
    :return: A success or error response.
    """
    # Determine if the entity is a user or a company
    user = User.query.get(entity_id)
    company = None

    if user:
        # Update credits for a user
        credit = Credit.query.filter_by(user_id=entity_id).first()
        if not credit:
            # Create a new Credit entry if none exists
            credit = Credit(user_id=entity_id, credit_count=credit_count)
            db.session.add(credit)
        else:
            credit.credit_count = credit_count

        db.session.commit()
        return {
            'message': f'Credits updated successfully for user {user.username}',
            'current_credits': credit.credit_count
        }

    # If no user is found, check if it's a company
    company = Company.query.get(entity_id)
    if company:
        # Update credits for a company
        credit = Credit.query.filter_by(company_id=entity_id).first()
        if not credit:
            # Create a new Credit entry if none exists
            credit = Credit(company_id=entity_id, credit_count=credit_count)
            db.session.add(credit)
        else:
            credit.credit_count = credit_count

        db.session.commit()
        return {
            'message': f'Credits updated successfully for company {company.name}',
            'current_credits': credit.credit_count
        }

    # If neither user nor company is found
    return {'error': 'Entity not found'}, 404

def get_remaining_credits(user_id):
    """
    Fetch the remaining credits for a user or their associated company.

    :param user_id: ID of the user
    :return: Total remaining credits
    """
    # Fetch the user object
    user = User.query.get(user_id)
    if not user:
        return None  # User not found

    if user.company_id:
        # If the user is associated with a company, aggregate company credits
        credit_entry = Credit.query.filter_by(company_id=user.company_id).first()
        if credit_entry:
            return credit_entry.credit_count
    else:
        # If the user is a personal user, fetch user-specific credits
        credit_entry = Credit.query.filter_by(user_id=user_id).first()
        if credit_entry:
            return credit_entry.credit_count

    return 0  # No credits found for the user or company
