from modules.models.credit import Credit
from extensions import db

def update_credits(entity_id, is_company, credit_increment):
    if is_company:
        credit = Credit.query.filter_by(company_id=entity_id).first()
    else:
        credit = Credit.query.filter_by(user_id=entity_id).first()

    if not credit:
        return {'error': 'Entity not found'}, 404

    credit.credit_count += credit_increment
    db.session.commit()
    return {
        'message': 'Credits updated successfully',
        'current_credits': credit.credit_count
    }
