# backend\modules\routes\admin_routes.py
from flask import Blueprint, request, jsonify
from extensions import db
from modules.logging_util import setup_logger
from modules.services.user_service import create_user
from modules.services.company_service import create_company

logger = setup_logger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/add-company', methods=['POST'])
def add_company():
    data = request.json
    company_name = data.get('company_name')
    admin_username = data.get('username')
    admin_email = data.get('email')
    admin_password = data.get('password')
    logger.info(f"Provided company data: {data}")

    if not (company_name and admin_username and admin_email and admin_password):
        return jsonify({"message": "All fields are required"}), 400

    try:
        # Create the company
        company_response, company_status = create_company(company_name, 10)
        if company_status != 201:
            return jsonify(company_response), company_status

        # Retrieve the created company ID
        company_id = company_response.get("company_id")

        # Create the admin user
        admin_response = create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            company_id=company_id
        )

        # Handle errors during user creation
        if 'error' in admin_response:
            logger.error(f"Error creating special admin: {admin_response['error']}")
            return jsonify(admin_response), 400

        # Commit the admin user
        db.session.commit()
        return jsonify({"message": "Company and admin created successfully"}), 201

    except Exception as e:
        logger.error(f"Exception during company and admin creation: {str(e)}")
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

