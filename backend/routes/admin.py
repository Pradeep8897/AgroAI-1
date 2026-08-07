from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models.orm_models import (
    Booking,
    Crop,
    DiseaseReport,
    Equipment,
    LoginAttempt,
    LoginSession,
    Order,
    Product,
    User,
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_stats():
    try:
        total_users = User.query.count()
        active_sessions = LoginSession.query.filter_by(active=True).count()
        total_login_attempts = LoginAttempt.query.count()
        successful_logins = LoginAttempt.query.filter_by(success=True).count()
        failed_logins = LoginAttempt.query.filter_by(success=False).count()
        last_login = (
            LoginAttempt.query.filter_by(success=True)
            .order_by(LoginAttempt.created_at.desc())
            .first()
        )
        last_login_time = last_login.created_at.isoformat() if last_login else None

        total_bookings = Booking.query.count()
        booking_revenue = float(Booking.query.with_entities(db.func.coalesce(db.func.sum(Booking.total_cost), 0)).scalar() or 0.0)
        total_products = Product.query.count()
        total_orders = Order.query.count()
        order_revenue = float(Order.query.with_entities(db.func.coalesce(db.func.sum(Order.total_cost), 0)).scalar() or 0.0)
        total_crops_logged = Crop.query.count()
        total_diseases_scanned = DiseaseReport.query.count()

        recent_users = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            for user in User.query.order_by(User.created_at.desc()).limit(10).all()
        ]

        recent_bookings = [
            {
                "id": booking.id,
                "username": booking.user.username if booking.user else None,
                "equipment_name": booking.equipment.name if booking.equipment else None,
                "hours": booking.hours,
                "total_cost": float(booking.total_cost or 0.0),
                "status": booking.status,
                "date": booking.date,
            }
            for booking in (
                Booking.query
                .join(User, Booking.user_id == User.id)
                .join(Equipment, Booking.equipment_id == Equipment.id)
                .order_by(Booking.created_at.desc())
                .limit(10)
                .all()
            )
        ]

        login_history = [
            {
                "user_id": entry.user_id,
                "email": entry.email,
                "success": bool(entry.success),
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in LoginAttempt.query.order_by(LoginAttempt.created_at.desc()).limit(10).all()
        ]

        return jsonify({
            "success": True,
            "metrics": {
                "total_users": total_users,
                "active_users": active_sessions,
                "online_users": active_sessions,
                "total_login_attempts": total_login_attempts,
                "successful_logins": successful_logins,
                "failed_logins": failed_logins,
                "last_login_time": last_login_time,
                "total_bookings": total_bookings,
                "booking_revenue": round(booking_revenue, 2),
                "total_products": total_products,
                "total_orders": total_orders,
                "order_revenue": round(order_revenue, 2),
                "total_crops_logged": total_crops_logged,
                "total_diseases_scanned": total_diseases_scanned,
                "total_platform_revenue": round(booking_revenue + order_revenue, 2),
            },
            "recent_users": recent_users,
            "recent_bookings": recent_bookings,
            "login_history": login_history,
        })
    except Exception as error:
        current_app.logger.exception("Error loading admin stats")
        return jsonify({"success": False, "message": "Unable to load admin statistics."}), 500
