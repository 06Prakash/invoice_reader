from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
import razorpay
import os
from decimal import Decimal
from modules.logging_util import setup_logger
from modules.services.credit_service import update_credit, get_remaining_credits

logger = setup_logger()
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

razor_bp = Blueprint('razor', __name__)

@razor_bp.route('/initiate-payment', methods=['POST'])
@jwt_required()
def initiate_payment():
    """
    Initiates a payment request with Razorpay.
    """
    data = request.json
    amount = data.get('amount', 0)  # Amount in INR

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    user_id = get_jwt_identity()  # Securely fetch the user ID from the JWT
    try:
        # Create Razorpay order
        order = razorpay_client.order.create({
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1  # Auto-capture payment
        })
        logger.info(f"Payment order created for user {user_id}: {order['id']}")

        # Return order details to the frontend
        return jsonify(order), 200
    except Exception as e:
        logger.error(f"Error creating Razorpay order for user {user_id}: {str(e)}")
        return jsonify({"error": "Failed to create payment order"}), 500

@razor_bp.route("/get-key", methods=["GET"])
def get_razorpay_key():
    """
    Endpoint to fetch the Razorpay key dynamically.
    Returns the key from environment variables.
    """
    key = os.getenv("RAZORPAY_KEY_ID")
    if not key:
        return jsonify({"error": "Razorpay key not found"}), 500
    return jsonify({"key": key}), 200

@razor_bp.route("/payment-success", methods=["POST"])
@jwt_required()
def payment_success():
    """
    Handle Razorpay payment success callback and ensure credits are updated.
    If credits update fails, initiate a refund.
    """
    data = request.json
    payment_id = data.get("payment_id")
    order_id = data.get("order_id")
    signature = data.get("signature")
    amount = data.get("amount", 0)  # Amount in paise

    if not payment_id or not order_id or not signature or not amount:
        return jsonify({"error": "Missing payment details"}), 400

    user_id = get_jwt_identity()

    try:
        # Verify the payment using Razorpay SDK
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })

        # Convert amount to Decimal for accurate calculations
        amount_in_inr = Decimal(amount) / 100

        # Deduct 2% transaction fee
        amount_after_fee = amount_in_inr * Decimal("0.98")

        # Calculate credits to add (₹10 = 1 credit)
        credits_to_add = amount_after_fee / Decimal("10.00")
        if credits_to_add <= Decimal("0.00"):
            raise ValueError(f"Invalid credit amount. Amount after fee: {amount_after_fee}")

        # Get remaining credits and add the calculated credits
        remaining_credits = Decimal(get_remaining_credits(user_id) or 0)
        total_credits = credits_to_add + remaining_credits

        logger.info(f"Credits to add: {credits_to_add}, Remaining credits: {remaining_credits}")

        # Update user credits in the database
        update_credit(user_id, total_credits)

        logger.info(f"Added {credits_to_add} credits to user {user_id}. Total credits: {total_credits}")
        return jsonify({"message": "Credits updated successfully"}), 200

    except Exception as e:
        logger.error(f"Failed to update credits for user {user_id}: {str(e)}")

        # Attempt to issue a refund
        try:
            refund = razorpay_client.payment.refund(payment_id, {
                "amount": int(amount),  # Refund the full amount in paise
                "speed": "optimum",  # Attempt the refund at the optimum speed
            })
            logger.info(f"Refund initiated for payment {payment_id} for user {user_id}: {refund}")
            return jsonify({"error": "Failed to update credits. Refund initiated.", "refund": refund}), 500
        except Exception as refund_error:
            logger.error(f"Failed to issue refund for payment {payment_id}: {str(refund_error)}")
            return jsonify({"error": "Failed to update credits and refund. Please contact support."}), 500
