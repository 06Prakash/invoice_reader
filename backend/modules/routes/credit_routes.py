from flask import Blueprint, request, jsonify
from modules.services.credit_service import update_credit, get_remaining_credits
from modules.middleware.admin_middleware import special_admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity

credit_routes = Blueprint('credit_routes', __name__)

@credit_routes.route('/update', methods=['PUT'])
@special_admin_required
def update_credit_endpoint():
    """
    Update credit count for a user or company.
    """
    data = request.json
    entity_id = data.get('entityId')
    credit_count = data.get('creditCount')

    if entity_id is None or credit_count is None:
        return jsonify({'error': 'entityId and creditCount are required fields'}), 400

    response = update_credit(entity_id, credit_count)
    return jsonify(response), 200

@credit_routes.route('/remaining', methods=['GET'])
@jwt_required()
def get_remaining_credits_endpoint():
    """
    Get the remaining credits for the logged-in user.
    """
    user_id = get_jwt_identity()
    remaining_credits = get_remaining_credits(user_id)

    if remaining_credits is None:
        return jsonify({'error': 'Credits not found'}), 404

    return jsonify({'remaining_credits': remaining_credits}), 200