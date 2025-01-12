from flask import Blueprint, request, jsonify
from flask_mail import Mail, Message
from flask_jwt_extended import create_access_token, create_refresh_token
from modules.logging_util import setup_logger
logger = setup_logger(__name__)
import os
from modules.services.auth_services import generate_and_store_otp, is_otp_valid, set_password
from modules.services.user_service import is_email_registered, get_user_by_email  # Import the new function

# Initialize the Blueprint
auth_bp = Blueprint('auth', __name__)

# Flask-Mail and other global configurations
mail = Mail()

# Route to send OTP
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Check if the email exists in the database
    if not is_email_registered(email):
        return jsonify({"error": "Email not registered"}), 404

    try:
        # Generate and store OTP
        otp = generate_and_store_otp(email)

        # Send OTP via email
        msg = Message(
            "Your OTP Code",
            sender=os.getenv('MAIL_USERNAME'),  # Use MAIL_USERNAME from the config
            recipients=[email]
        )
        msg.body = f"Your OTP code is {otp}. It is valid for 5 minutes."
        mail.send(msg)

        return jsonify({"message": "OTP sent successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

# Route to verify OTP
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    # Check if the email exists in the database
    if not is_email_registered(email):
        return jsonify({"error": "Email not registered"}), 404

    try:
        # Retrieve user and verify OTP
        user = get_user_by_email(email)

        if user and is_otp_valid(user.otp_code, user.otp_created_at, otp):
            # Create the access token with additional claims
            access_token = create_access_token(
                identity=str(user.id),  # Convert user ID to string explicitly
                additional_claims={
                    'special_admin': user.special_admin,  # Add special_admin status to the token
                    'company': user.company.name if user.company else None  # Add company name if available
                }
            )

            # Create the refresh token
            refresh_token = create_refresh_token(identity=str(user.id))

            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,  # Include refresh token in the response
                'special_admin': user.special_admin,  # Include special_admin in the response
                'username': user.username,  # Include username for personalization
                "message": "OTP verified successfully"
            }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    logger.info(f"Received data:{data}")
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('newPassword')

    if not email or not otp or not new_password:
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Fetch user details
        from modules.services.user_service import get_user_by_email
        user = get_user_by_email(email)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Validate OTP
        if not is_otp_valid(user.otp_code, user.otp_created_at, otp):
            return jsonify({"error": "Invalid or expired OTP"}), 400

        # Update password
        set_password(email, new_password)
        return jsonify({"message": "Password updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to reset password"}), 500

