from flask import Blueprint, request, jsonify
import os
from backend.models.user import UserModel
from werkzeug.security import check_password_hash
from backend.utils.jwt_handler import JWTHandler, require_auth
from backend.extensions import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json() or {}

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'farmer')

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required."
        }), 400

    existing = UserModel.get_user_by_email(email)

    if existing:
        return jsonify({
            "success": False,
            "message": "Email already registered."
        }), 400

    user_id = UserModel.create_user(username, email, password, role)

    if user_id:
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "role": role
            }
        }), 201

    return jsonify({
        "success": False,
        "message": "Registration failed."
    }), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():

    data = request.get_json() or {}

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    user = UserModel.get_user_by_email(email)

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid credentials."
        }), 401

    if not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Invalid credentials."
        }), 401

    # Generate secure JWT token
    token = JWTHandler.generate_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"]
    )

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 200


@auth_bp.route('/api/auth/profile', methods=['GET', 'PUT'])
@require_auth(allowed_roles=['user', 'admin', 'farmer', 'expert'])
def profile():

    user_id = request.user_id

    if request.method == "GET":

        user = UserModel.get_user_by_id(user_id)

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "phone": user.get("phone", ""),
                "location": user.get("location", ""),
                "state": user.get("state", ""),
                "farm_size": user.get("farm_size", ""),
                "language": user.get("language", "")
            }
        })

    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone", "")
    location = data.get("location", "")
    state = data.get("state", "")
    farm_size = data.get("farm_size", "")
    language = data.get("language", "")

    if not username or not email:
        return jsonify({
            "success": False,
            "message": "Username and email are required."
        }), 400

    try:
        farm_size = float(farm_size) if farm_size else None
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Farm size must be a number."
        }), 400

    success = UserModel.update_profile(
        user_id,
        username,
        email,
        phone,
        location,
        state,
        farm_size,
        language
    )

    if success:

        updated_user = UserModel.get_user_by_id(user_id)

        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "user": updated_user
        })

    return jsonify({
        "success": False,
        "message": "Profile update failed."
    }), 500


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")
def forgot_password():

    data = request.get_json() or {}

    email = data.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400
    # Find user but don't reveal existence to prevent user enumeration
    user = UserModel.get_user_by_email(email)

    if user:
        # Generate a short-lived reset token
        token = JWTHandler.generate_reset_token(user['id'], expires_in_minutes=30)
        frontend = os.environ.get('FRONTEND_URL', '')
        reset_url = f"{frontend}/reset-password?token={token}" if frontend else None
        # In development/test mode, allow returning token for manual testing
        if os.environ.get('DEV_SEND_RESET_TOKEN') == '1':
            return jsonify({
                "success": True,
                "message": "Password reset token generated (dev).",
                "reset_token": token,
                "reset_url": reset_url
            }), 200

        # Attempt to send the reset email using SMTP
        from backend.utils.emailer import send_reset_email
        sent = False
        if reset_url:
            try:
                sent = send_reset_email(email, reset_url)
            except Exception as ex:
                print(f"Email delivery failed: {ex}")
        if not sent:
            # Fallback: log token for operators (safe in internal logs)
            print(f"Password reset token for {email}: {token}")

    # Always return a generic success message
    return jsonify({
        "success": True,
        "message": "If the email exists, a password reset link has been sent."
    }), 200


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({"success": False, "message": "Token and new password are required."}), 400

    payload = JWTHandler.verify_reset_token(token)
    if not payload:
        return jsonify({"success": False, "message": "Invalid or expired token."}), 400

    user_id = payload.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Invalid token payload."}), 400

    success = UserModel.update_password(user_id, new_password)
    if not success:
        return jsonify({"success": False, "message": "Failed to update password."}), 500

    return jsonify({"success": True, "message": "Password updated successfully."}), 200