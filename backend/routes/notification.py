from flask import Blueprint, jsonify, request
from backend.models.notification import NotificationModel
from backend.utils.jwt_handler import require_auth

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/api/notifications', methods=['GET'])
@require_auth(allowed_roles=['user', 'farmer', 'expert', 'admin'])
def get_notifications():
    user_id = request.user_id
    alerts = NotificationModel.get_active_alerts(user_id)
    return jsonify({
        "success": True,
        "notifications": alerts
    })
