from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify
from modules.models.user import User

def special_admin_required(func):
    """
    Decorator to restrict access to special_admin users.
    """
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.special_admin:
            return jsonify({'error': 'Access denied. Special admin only.'}), 403

        return func(*args, **kwargs)

    return wrapper
