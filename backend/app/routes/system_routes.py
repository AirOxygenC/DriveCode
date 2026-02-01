from flask import Blueprint, jsonify

system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "voice-loop-backend"}), 200
