from datetime import datetime, timedelta
from extensions import bcrypt, db
import random
from modules.models.user import User

def hash_password(password):
    """Generate a hashed password."""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    """Verify the provided password against the stored hash."""
    return bcrypt.check_password_hash(hashed_password, password)

def generate_otp():
    """Generate a 6-digit OTP."""
    return f"{random.randint(100000, 999999)}"

def is_otp_valid(otp_code, otp_created_at, provided_otp, expiration_minutes=5):
    """
    Check if the provided OTP is valid.
    - Verifies that the OTP matches and is within the expiration time.
    """
    if otp_code == provided_otp:
        if otp_created_at and (datetime.utcnow() - otp_created_at) <= timedelta(minutes=expiration_minutes):
            return True
    return False

def increment_attempts(current_attempts):
    """Increment the count of OTP attempts."""
    return current_attempts + 1

def generate_and_store_otp(email):
    """
    Generate an OTP and store it in the user's record.

    :param email: The email of the user.
    :return: The generated OTP.
    :raises ValueError: If the user is not found.
    """
    from modules.services.user_service import get_user_by_email  # Import user service
    user = get_user_by_email(email)
    if not user:
        raise ValueError("User not found")

    # Generate OTP
    otp = generate_otp()
    user.otp_code = otp
    user.otp_created_at = datetime.utcnow()

    # Commit changes to the database
    db.session.commit()

    return otp

def set_password(email, new_password):
    """
    Update the user's password.

    :param email: The email of the user.
    :param new_password: The new password to set.
    :raises ValueError: If the user is not found.
    """
    from modules.services.user_service import get_user_by_email  # Import user service
    user = get_user_by_email(email)
    if not user:
        raise ValueError("User not found")

    # Hash and update the password
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

    # Reset OTP fields
    user.otp_code = None
    user.otp_created_at = None

    # Commit changes to the database
    db.session.commit()
