import time
from flask import jsonify, Blueprint

health_bp = Blueprint('health', __name__)

# Track first health check
health_check_data = {
    "first_check_time": None,
    "subsequent_delay": 120  # Subsequent delay in seconds (2 minutes)
}

@health_bp.route('/check', methods=['GET'])
def health_check():
    current_time = time.time()
    if not health_check_data["first_check_time"]:
        health_check_data["first_check_time"] = current_time
        return jsonify({"status": "healthy", "check_type": "first"}), 200
    
    # Enforce delay for subsequent checks
    elapsed = current_time - health_check_data["first_check_time"]
    if elapsed >= health_check_data["subsequent_delay"]:
        return jsonify({"status": "healthy", "check_type": "subsequent"}), 200
    
    return jsonify({"status": "waiting", "time_remaining": health_check_data["subsequent_delay"] - elapsed}), 429
