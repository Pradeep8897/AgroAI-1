"""
JWT Token Handler - Secure token generation and verification
Replaces the insecure mock token system
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required for secure token handling.")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

class JWTHandler:
    """Handle JWT token generation and verification"""
    
    @staticmethod
    def generate_token(user_id, email, role, expires_in_hours=TOKEN_EXPIRY_HOURS):
        """
        Generate a secure JWT token
        
        Args:
            user_id: Unique user identifier
            email: User email address
            role: User role (user, admin, etc)
            expires_in_hours: Token expiration time in hours
            
        Returns:
            JWT token string
        """
        try:
            payload = {
                'user_id': int(user_id),
                'email': email,
                'role': role,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except Exception as e:
            raise ValueError(f"Token generation failed: {str(e)}")
    
    @staticmethod
    def verify_token(token):
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dict if valid, None if invalid
        """
        try:
            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Token invalid
        except Exception:
            return None  # Other errors
    
    @staticmethod
    def get_token_from_request():
        """
        Extract token from Authorization header
        
        Returns:
            Token string or None
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]


    @staticmethod
    def generate_reset_token(user_id, expires_in_minutes=30):
        """
        Generate a short-lived token used for password resets.
        """
        try:
            payload = {
                'user_id': int(user_id),
                'type': 'pwd_reset',
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except Exception:
            return None

    @staticmethod
    def verify_reset_token(token):
        """Verify a password-reset token and return payload or None."""
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get('type') != 'pwd_reset':
                return None
            return payload
        except Exception:
            return None


def require_auth(allowed_roles=None):
    """
    Decorator to require authentication on endpoints
    
    Args:
        allowed_roles: List of allowed roles (e.g., ['admin', 'user'])
                      If None, any authenticated user is allowed
    
    Usage:
        @app.route('/api/protected', methods=['GET'])
        @require_auth(allowed_roles=['admin', 'user'])
        def protected_endpoint():
            user_id = request.user_id
            user_email = request.user_email
            user_role = request.user_role
            return {'message': f'Hello {user_email}'}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from request
            token = JWTHandler.get_token_from_request()
            if not token:
                return jsonify({'error': 'Missing authorization token'}), 401
            
            # Verify token
            payload = JWTHandler.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Check role if specified
            if allowed_roles and payload.get('role') not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Attach user info to request object
            request.user_id = payload.get('user_id')
            request.user_email = payload.get('email')
            request.user_role = payload.get('role')
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
