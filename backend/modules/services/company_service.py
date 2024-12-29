# backend/modules/services/company_service.py
from extensions import db
from modules.models.company import Company

def update_company_credits(company_id, credit_increment):
    company = Company.query.get(company_id)
    if not company:
        return {'error': 'Company not found'}, 404

    company.credit_count += credit_increment
    db.session.commit()
    return {'message': 'Company credits updated successfully', 'current_credits': company.credit_count}

