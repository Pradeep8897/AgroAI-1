from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from backend.models.user import UserModel
from backend.utils.jwt_handler import JWTHandler, require_auth
from backend.extensions import limiter
from backend.database.mysql_connection import get_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/api/admin/login", methods=["POST"])
@limiter.limit("5 per minute")
def admin_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    user = UserModel.get_user_by_email(email)
    if not user or user.get("role") != "admin" or not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Invalid admin credentials"
        }), 401

    token = JWTHandler.generate_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"]
    )

    return jsonify({
        "success": True,
        "token": token
    })

@admin_bp.route('/api/admin/stats', methods=['GET'])
@require_auth(allowed_roles=['admin'])
def get_stats():
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # 2. Total bookings
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cursor.fetchone()[0]
        
        # 3. Sum of booking revenues
        cursor.execute("SELECT SUM(total_cost) FROM bookings")
        booking_revenue = cursor.fetchone()[0] or 0.0

        # 4. Total products
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]

        # 5. Total orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        # 6. Sum of order revenue
        cursor.execute("SELECT SUM(total_cost) FROM orders")
        order_revenue = cursor.fetchone()[0] or 0.0

        # 7. Total Crop recommendations logged
        cursor.execute("SELECT COUNT(*) FROM crops")
        total_crops_logged = cursor.fetchone()[0]

        # 8. Total disease scans completed
        cursor.execute("SELECT COUNT(*) FROM disease_reports")
        total_diseases_scanned = cursor.fetchone()[0]

        # Fetch recent users list for table
        cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 10")
        users_rows = cursor.fetchall()
        
        if is_sqlite:
            recent_users = [dict(r) for r in users_rows]
        else:
            recent_users = [{
                "id": r[0],
                "username": r[1],
                "email": r[2],
                "role": r[3],
                "created_at": r[4]
            } for r in users_rows]

        # Fetch recent equipment bookings for log
        cursor.execute("""
            SELECT b.id, u.username, e.name as equipment_name, b.hours, b.total_cost, b.status, b.date 
            FROM bookings b 
            JOIN users u ON b.user_id = u.id 
            JOIN equipment e ON b.equipment_id = e.id 
            ORDER BY b.created_at DESC LIMIT 10
        """)
        booking_rows = cursor.fetchall()
        
        recent_bookings = []
        for r in booking_rows:
            if is_sqlite:
                recent_bookings.append(dict(r))
            else:
                recent_bookings.append({
                    "id": r[0],
                    "username": r[1],
                    "equipment_name": r[2],
                    "hours": r[3],
                    "total_cost": r[4],
                    "status": r[5],
                    "date": r[6]
                })

        return jsonify({
            "success": True,
            "metrics": {
                "total_users": total_users,
                "total_bookings": total_bookings,
                "booking_revenue": round(booking_revenue, 2),
                "total_products": total_products,
                "total_orders": total_orders,
                "order_revenue": round(order_revenue, 2),
                "total_crops_logged": total_crops_logged,
                "total_diseases_scanned": total_diseases_scanned,
                "total_platform_revenue": round(booking_revenue + order_revenue, 2)
            },
            "recent_users": recent_users,
            "recent_bookings": recent_bookings
        })
        
    except Exception as e:
        print(f"Error loading admin stats: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()
