from extensions import app
from modules.services.company_service import create_company
from modules.services.user_service import create_user
import argparse


def create_special_admin(company_name, admin_username, admin_email, admin_password):
    """
    Creates a special admin and associates them with a company.
    
    Args:
        company_name (str): Name of the company.
        admin_username (str): Username for the special admin.
        admin_email (str): Email for the special admin.
        admin_password (str): Password for the special admin.

    Returns:
        str: Success or error message.
    """
    # Step 1: Create or retrieve the company
    company_response, status_code = create_company(name=company_name, initial_credits=0.00)
    if status_code != 201:
        return f"Error creating company: {company_response.get('error')}"

    company_id = company_response.get('company_id')

    # Step 2: Create the special admin user
    user_response = create_user(
        username=admin_username,
        email=admin_email,
        password=admin_password,
        company_id=company_id
    )

    if 'error' in user_response:
        return f"Error creating special admin: {user_response['error']}"

    return f"Special admin '{admin_username}' created successfully for company '{company_name}'."


if __name__ == "__main__":
    # Setup argument parsing
    parser = argparse.ArgumentParser(description="Create a special admin and associate them with a company.")
    parser.add_argument("--company", required=True, help="Name of the company.")
    parser.add_argument("--username", required=True, help="Username of the special admin.")
    parser.add_argument("--email", required=True, help="Email of the special admin.")
    parser.add_argument("--password", required=True, help="Password for the special admin.")

    args = parser.parse_args()

    # Run the script within the application context
    with app.app_context():
        result = create_special_admin(args.company, args.username, args.email, args.password)
        print(result)
