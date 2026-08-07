from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models.orm_models import LoginAttempt, LoginSession, User


auth_bp = Blueprint("auth", __name__)


def _parse_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def _parse_user_id_from_token(token):
    if token and token.startswith("mock-jwt-token-"):
        payload = token[len("mock-jwt-token-"):]
        # payload format: <user_id>-<role>, but user_id may contain hyphens (UUID),
        # so split from the right to separate role.
        if '-' in payload:
            user_part, _role = payload.rsplit('-', 1)
            return user_part
        return payload
    return None


def _serialize_user(user):
    return {
        "id": str(user.id) if user.id else None,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "phone": user.phone or "",
        "location": user.location or "",
        "state": user.state or "",
        "farm_size": user.farm_size if user.farm_size is not None else "",
        "language": user.language or "",
    }


def _record_login_attempt(email, user_id, success):
    try:
        db.session.add(LoginAttempt(email=email, user_id=user_id, success=success))
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        print(f"Error recording login attempt: {error}")


def _create_login_session(user_id, session_token):
    try:
        db.session.add(LoginSession(user_id=user_id, session_token=session_token, active=True))
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        print(f"Error creating login session: {error}")


def _deactivate_login_session(user_id=None, session_token=None):
    if not user_id and not session_token:
        return

    try:
        query = LoginSession.query.filter_by(active=True)
        if user_id and session_token:
            query = query.filter((LoginSession.user_id == user_id) | (LoginSession.session_token == session_token))
        elif user_id:
            query = query.filter_by(user_id=user_id)
        else:
            query = query.filter_by(session_token=session_token)

        for session in query.all():
            session.active = False
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        print(f"Error deactivating login session: {error}")


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username") or data.get("name") or (data.get("email", "").split("@")[0] if data.get("email") else None)
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "farmer")

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400


    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already registered."}), 400

    try:
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "user": {"id": str(user.id), "username": user.username, "email": user.email, "role": user.role},
        }), 201
    except Exception as error:
        db.session.rollback()
        print(f"Registration failed: {error}")
        return jsonify({"success": False, "message": "Registration failed."}), 500


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        _record_login_attempt(email, None, False)
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    if not check_password_hash(user.password, password):
        _record_login_attempt(email, user.id, False)
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    token = f"mock-jwt-token-{user.id}-{user.role}"
    _record_login_attempt(email, user.id, True)
    _create_login_session(user.id, token)

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    token = _parse_bearer_token()
    user_id = _parse_user_id_from_token(token)
    if not token or not user_id:
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    _deactivate_login_session(user_id=user_id, session_token=token)
    return jsonify({"success": True, "message": "Logged out successfully."}), 200


@auth_bp.route("/api/auth/profile", methods=["GET", "PUT"])
def profile():
    user_id = _parse_user_id_from_token(_parse_bearer_token())
    if not user_id:
        user_id = request.args.get("user_id") or (request.get_json() or {}).get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    if request.method == "GET":
        return jsonify({"success": True, "user": _serialize_user(user)})

    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    if not username or not email:
        return jsonify({"success": False, "message": "Username and email are required."}), 400

    try:
        farm_size = float(data["farm_size"]) if data.get("farm_size") else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Farm size must be a number."}), 400

    duplicate = User.query.filter(User.email == email, User.id != user.id).first()
    if duplicate:
        return jsonify({"success": False, "message": "Email already registered."}), 400

    user.username = username
    user.email = email
    user.phone = data.get("phone", "")
    user.location = data.get("location", "")
    user.state = data.get("state", "")
    user.farm_size = farm_size
    user.language = data.get("language", "")

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "user": _serialize_user(user),
        })
    except Exception as error:
        db.session.rollback()
        print(f"Profile update failed: {error}")
        return jsonify({"success": False, "message": "Profile update failed."}), 500


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    if not User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email address not found."}), 404

    return jsonify({
        "success": True,
        "message": "Password reset instructions have been sent to your email.",
    }), 200
