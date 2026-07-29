# AgroAI Security Remediation Guide

**Purpose:** Step-by-step instructions to fix all identified security vulnerabilities  
**Audience:** Development Team  
**Estimated Time:** 2-3 weeks for critical fixes, 6 weeks for complete remediation

---

## Table of Contents

1. [Quick Start (Critical Fixes)](#quick-start)
2. [Authentication System Overhaul](#authentication-overhaul)
3. [Authorization & Access Control](#authorization)
4. [Input Validation Framework](#input-validation)
5. [Security Headers & CORS](#security-headers)
6. [Dependency & Configuration Management](#dependencies)
7. [Testing & Validation](#testing)
8. [Deployment Checklist](#deployment)

---

## Quick Start (Critical Fixes)

### Step 0: Environment Setup

```bash
# Create a security branch
git checkout -b security/fix-critical-vulnerabilities

# Install development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install PyJWT flask-limiter werkzeug
```

### Step 1: Create JWT Authentication Module (Day 1)

Create `backend/auth/jwt_handler.py`:

```python
"""
JWT Authentication Handler
Replaces the broken mock JWT system
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import uuid

# Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

if not SECRET_KEY:
    if os.environ.get('ENVIRONMENT') == 'production':
        raise EnvironmentError(
            'JWT_SECRET_KEY environment variable must be set in production!'
        )
    # Development default
    SECRET_KEY = 'dev-secret-change-in-production'
    print("⚠️  WARNING: Using development JWT secret key!")


def generate_token(user_id, role, email):
    """
    Generate a proper JWT token with signature validation
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow(),
        'jti': str(uuid.uuid4()),  # Token ID for revocation
        'type': 'access'
    }
    
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        print(f"Token generation error: {str(e)}")
        return None


def verify_token(token):
    """
    Verify JWT token and return payload
    Returns None if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        # Check if token is revoked (implement later)
        # if TokenBlacklist.is_revoked(payload['jti']):
        #     return None
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidSignatureError:
        print("Invalid token signature")
        return None
    except jwt.DecodeError:
        print("Failed to decode token")
        return None
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None


def require_auth(allowed_roles=None):
    """
    Decorator to require authentication on endpoints
    
    Usage:
        @require_auth()  # Any authenticated user
        @require_auth(allowed_roles=['admin'])  # Only admin users
        @require_auth(allowed_roles=['admin', 'farmer'])  # Multiple roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    "success": False,
                    "message": "Missing or invalid Authorization header"
                }), 401
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = verify_token(token)
            
            if not payload:
                return jsonify({
                    "success": False,
                    "message": "Invalid or expired token"
                }), 401
            
            # Check role if specified
            if allowed_roles and payload.get('role') not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "Insufficient permissions"
                }), 403
            
            # Pass payload as first argument
            return f(payload, *args, **kwargs)
        
        return decorated_function
    return decorator


def require_same_user(user_id_param='user_id'):
    """
    Decorator to ensure user can only access their own data
    
    Usage:
        @require_same_user()  # Gets user_id from 'user_id' query/body param
        @require_same_user('profile_id')  # Gets user_id from specific param
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Must have authentication first
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({"success": False, "message": "Unauthorized"}), 401
            
            token = auth_header[7:]
            payload = verify_token(token)
            if not payload:
                return jsonify({"success": False, "message": "Invalid token"}), 401
            
            # Get requested user_id from either query params or JSON body
            requested_user_id = request.args.get(user_id_param) or \
                              (request.get_json() or {}).get(user_id_param)
            
            # Convert to int for comparison
            try:
                requested_user_id = int(requested_user_id)
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Invalid user ID"}), 400
            
            # Verify token's user_id matches requested user_id
            # (unless user is admin)
            if payload['user_id'] != requested_user_id and payload.get('role') != 'admin':
                return jsonify({
                    "success": False,
                    "message": "Cannot access other user's data"
                }), 403
            
            # Pass payload as first argument
            return f(payload, *args, **kwargs)
        
        return decorated_function
    return decorator
```

### Step 2: Update Login Endpoint (Day 1)

Replace `backend/routes/auth.py` login function:

```python
from backend.auth.jwt_handler import generate_token, verify_token, require_auth

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password required"
        }), 400
    
    # Check credentials
    user = UserModel.get_user_by_email(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401
    
    # Generate proper JWT token
    token = generate_token(user['id'], user['role'], user['email'])
    if not token:
        return jsonify({
            "success": False,
            "message": "Failed to generate token"
        }), 500
    
    # Log the login (audit trail)
    AuditLog.log_event(user['id'], 'AUTH', 'user', 'login', 'success', 
                      f"from IP {request.remote_addr}")
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "role": user['role'],
            "username": user.get('username')
        }
    }), 200
```

### Step 3: Fix Profile Endpoints (Day 1)

Replace profile endpoint in `backend/routes/auth.py`:

```python
@auth_bp.route('/api/auth/profile', methods=['GET'])
@require_auth()
def get_profile(payload):
    """Get authenticated user's profile"""
    user_id = payload['user_id']  # From verified token!
    
    user = UserModel.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Don't expose password hash
    del user['password']
    
    return jsonify({
        "success": True,
        "user": user
    }), 200


@auth_bp.route('/api/auth/profile', methods=['PUT'])
@require_auth()
def update_profile(payload):
    """Update authenticated user's profile"""
    user_id = payload['user_id']  # From verified token!
    data = request.get_json() or {}
    
    # Only allow updating specific fields
    allowed_fields = ['username', 'phone', 'location', 'farm_size']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    # Validate input
    if not update_data:
        return jsonify({
            "success": False,
            "message": "No valid fields to update"
        }), 400
    
    # Update user
    success = UserModel.update_profile(user_id, update_data)
    if not success:
        return jsonify({
            "success": False,
            "message": "Failed to update profile"
        }), 500
    
    # Log the update
    AuditLog.log_event(user_id, 'PROFILE', 'user', 'update', 'success',
                      f"Updated: {', '.join(update_data.keys())}")
    
    return jsonify({
        "success": True,
        "message": "Profile updated successfully"
    }), 200
```

### Step 4: Fix CORS Configuration (Day 1)

Update `backend/app.py`:

```python
# Replace the wildcard CORS configuration
from flask_cors import CORS
import os

# Get allowed origins from environment
allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')

CORS(app, resources={
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,  # Set to true only if using cookies
        "max_age": 3600
    }
})

print(f"[!] CORS configured for origins: {allowed_origins}")
```

### Step 5: Add Authentication to Protected Endpoints (Day 2)

Apply `@require_auth()` to all protected endpoints:

```python
# In routes/crop.py
@crop_bp.route('/api/crop/recommend', methods=['POST'])
@require_auth()  # ADD THIS
def recommend_crop(payload):
    user_id = payload['user_id']  # Extract from token
    # ... rest of implementation

# In routes/disease.py
@disease_bp.route('/api/disease/detect', methods=['POST'])
@require_auth()  # ADD THIS
def detect_disease(payload):
    user_id = payload['user_id']
    # ... rest of implementation

# In routes/admin.py
@admin_bp.route('/api/admin/stats', methods=['GET'])
@require_auth(allowed_roles=['admin'])  # ADD THIS - requires admin role
def get_stats(payload):
    # ... rest of implementation
```

### Step 6: Remove Pickle Deserialization (Day 2)

Update `backend/routes/disease.py` and `backend/routes/crop.py`:

```python
# BEFORE (VULNERABLE):
import pickle
with open(disease_model_path, "rb") as f:
    disease_model = pickle.load(f)

# AFTER (SAFE):
import joblib  # Install: pip install joblib
disease_model = joblib.load(disease_model_path)

# Or for deep learning models:
from tensorflow import keras
disease_model = keras.models.load_model(disease_model_path)
```

---

## Authentication System Overhaul

### Create Token Blacklist for Logout

Create `backend/auth/token_blacklist.py`:

```python
"""
Token Blacklist Management
Tracks revoked tokens
"""

import os
from datetime import datetime

class TokenBlacklist:
    """
    Track revoked tokens (in-memory for development, Redis for production)
    """
    
    def __init__(self):
        self.blacklist = set()
        self.timestamps = {}
    
    def revoke(self, jti, reason=""):
        """Revoke a token by JTI"""
        self.blacklist.add(jti)
        self.timestamps[jti] = {
            'revoked_at': datetime.utcnow(),
            'reason': reason
        }
        print(f"[!] Token revoked: {jti} ({reason})")
    
    def is_revoked(self, jti):
        """Check if token is revoked"""
        return jti in self.blacklist
    
    def cleanup_expired(self, expiration_hours=24):
        """Remove expired tokens from memory"""
        # Cleanup logic for old revocations
        pass

# Global instance
blacklist = TokenBlacklist()
```

### Add Logout Endpoint

Add to `backend/routes/auth.py`:

```python
@auth_bp.route('/api/auth/logout', methods=['POST'])
@require_auth()
def logout(payload):
    """Revoke the current token"""
    from backend.auth.token_blacklist import blacklist
    
    # Revoke the token
    blacklist.revoke(payload['jti'], reason="user_logout")
    
    # Log the logout
    AuditLog.log_event(payload['user_id'], 'AUTH', 'user', 'logout', 'success')
    
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200
```

---

## Authorization & Access Control

### Fix IDOR on All Endpoints

Example for crop history:

```python
# BEFORE (VULNERABLE):
@crop_bp.route('/api/crop/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')  # From request!
    # Any user can query any user_id

# AFTER (SECURE):
@crop_bp.route('/api/crop/history', methods=['GET'])
@require_auth()
def get_history(payload):
    user_id = payload['user_id']  # From verified token!
    
    # Get only this user's history
    history = CropModel.get_user_history(user_id)
    return jsonify({
        "success": True,
        "history": history
    }), 200
```

Apply this pattern to:
- `/api/disease/reports` - Only return user's own reports
- `/api/bookings` - Only return user's own bookings
- `/api/orders` - Only return user's own orders
- `/api/notifications` - Only return user's own notifications

---

## Input Validation Framework

### Create Validation Module

Create `backend/validation/validators.py`:

```python
"""
Input validation utilities
"""

import math
import re
from datetime import datetime

class ValidationError(Exception):
    """Custom validation error"""
    pass

class FieldValidator:
    """Validate individual fields"""
    
    @staticmethod
    def validate_string(value, field_name, min_length=1, max_length=255):
        """Validate string field"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")
        
        if len(value) > max_length:
            raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
        
        return value.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email address")
        return email.lower()
    
    @staticmethod
    def validate_number(value, field_name, min_val=None, max_val=None, allow_float=False):
        """Validate numeric field"""
        try:
            if allow_float:
                num = float(value)
            else:
                num = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be numeric")
        
        # Check for NaN/Infinity
        if math.isnan(num) or math.isinf(num):
            raise ValidationError(f"{field_name} contains invalid value")
        
        if min_val is not None and num < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and num > max_val:
            raise ValidationError(f"{field_name} cannot exceed {max_val}")
        
        return num
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letter")
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain digit")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append("Password must contain special character")
        
        if errors:
            raise ValidationError("; ".join(errors))
        
        return password

# Usage example:
class CropRecommendationValidator:
    @staticmethod
    def validate_request(data):
        """Validate crop recommendation request"""
        try:
            return {
                'N': FieldValidator.validate_number(data.get('N', 0), 'N', min_val=0, max_val=300, allow_float=True),
                'P': FieldValidator.validate_number(data.get('P', 0), 'P', min_val=0, max_val=300, allow_float=True),
                'K': FieldValidator.validate_number(data.get('K', 0), 'K', min_val=0, max_val=300, allow_float=True),
                'ph': FieldValidator.validate_number(data.get('ph', 6.5), 'pH', min_val=4.0, max_val=9.0, allow_float=True),
                'temperature': FieldValidator.validate_number(data.get('temperature', 25), 'Temperature', min_val=-50, max_val=60, allow_float=True),
                'humidity': FieldValidator.validate_number(data.get('humidity', 50), 'Humidity', min_val=0, max_val=100, allow_float=True),
                'rainfall': FieldValidator.validate_number(data.get('rainfall', 500), 'Rainfall', min_val=0, max_val=10000, allow_float=True),
            }
        except ValidationError as e:
            raise ValidationError(str(e))
```

### Add File Upload Validation

Create `backend/validation/file_validators.py`:

```python
"""
File upload validation
"""

import os
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ALLOWED_IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

class FileValidator:
    @staticmethod
    def validate_image_upload(file, field_name='image'):
        """Validate image file upload"""
        errors = []
        
        if not file:
            errors.append(f"{field_name} is required")
            return errors
        
        if not file.filename:
            errors.append("File has no name")
            return errors
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        if file_size > MAX_FILE_SIZE:
            errors.append(f"File size must not exceed {MAX_FILE_SIZE / (1024*1024):.1f} MB")
        file.seek(0)
        
        # Check extension
        filename = secure_filename(file.filename)
        if '.' not in filename:
            errors.append("File must have an extension")
        else:
            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                errors.append(f"File type .{ext} not allowed. Use: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
        
        # Check MIME type
        if not file.content_type.startswith('image/'):
            errors.append(f"MIME type {file.content_type} not allowed. Must be image/*")
        elif file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
            errors.append(f"MIME type {file.content_type} not supported")
        
        return errors
```

---

## Security Headers & CORS

### Add Security Headers Middleware

Add to `backend/app.py`:

```python
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    
    # Prevent content type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # HSTS (HTTPS strict transport security)
    if os.environ.get('ENVIRONMENT') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    return response
```

---

## Dependency & Configuration Management

### Update Requirements.txt

```bash
# Remove any unsafe packages and pin versions
Flask==3.0.2
Flask-CORS==4.0.0
mysql-connector-python==8.3.0
werkzeug==3.0.1
PyJWT==2.8.1  # ADD: Proper JWT
requests==2.31.0
scikit-learn==1.4.0  # UPDATE: Check version
numpy==1.24.0  # UPDATE: Check version
pillow==10.1.0  # UPDATE: Check version
h5py==3.10.0  # UPDATE: Check version
flask-limiter==3.5.0  # ADD: Rate limiting
flask-talisman==1.1.0  # ADD: Security headers
joblib==1.3.2  # ADD: Safe model loading
gunicorn==21.2.0
```

### Environment Configuration

Create `.env.example`:

```bash
# REQUIRED - Set these before running
ENVIRONMENT=production  # or development
JWT_SECRET_KEY=your-secret-key-here-minimum-32-chars
DB_HOST=your-db-host
DB_USER=agroai_user  # Not root!
DB_PASSWORD=secure-password-here
DB_NAME=agroai

# OPTIONAL
CORS_ORIGINS=https://agroai.com,https://www.agroai.com
FLASK_DEBUG=False
LOG_LEVEL=INFO
```

---

## Testing & Validation

### Test Authentication

Create `backend/tests/test_auth.py`:

```python
"""
Test authentication system
"""

import pytest
from flask import Flask
from backend.app import create_app
from backend.auth.jwt_handler import generate_token, verify_token

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success(client):
    """Test successful login"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!!'
    })
    assert response.status_code == 200
    assert 'token' in response.json

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrong'
    })
    assert response.status_code == 401

def test_jwt_token_generation():
    """Test JWT token generation and verification"""
    token = generate_token(123, 'farmer', 'test@example.com')
    assert token is not None
    
    payload = verify_token(token)
    assert payload is not None
    assert payload['user_id'] == 123
    assert payload['role'] == 'farmer'

def test_jwt_token_invalid_signature():
    """Test that invalid signatures are rejected"""
    # Tamper with token
    token = generate_token(123, 'farmer', 'test@example.com')
    tampered = token[:-10] + '0000000000'  # Change last 10 chars
    
    payload = verify_token(tampered)
    assert payload is None  # Should be rejected

def test_protected_endpoint_requires_auth(client):
    """Test that protected endpoints require authentication"""
    response = client.get('/api/auth/profile')
    assert response.status_code == 401

def test_profile_endpoint_with_auth(client):
    """Test profile endpoint with authentication"""
    token = generate_token(123, 'farmer', 'test@example.com')
    response = client.get('/api/auth/profile',
        headers={'Authorization': f'Bearer {token}'}
    )
    # This will fail if user doesn't exist, but auth check passes
    assert response.status_code in [200, 404]  # Auth succeeded

def test_idor_protection(client):
    """Test that IDOR is prevented"""
    token = generate_token(123, 'farmer', 'test@example.com')  # User 123
    response = client.get('/api/auth/profile?user_id=999',  # Different user
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 403  # Should be forbidden
```

---

## Deployment Checklist

Before deploying to production, verify:

- [ ] ✅ All environment variables set (JWT_SECRET_KEY, DB credentials, etc.)
- [ ] ✅ JWT_SECRET_KEY is strong (minimum 32 random characters)
- [ ] ✅ CORS_ORIGINS set to actual domain, not localhost
- [ ] ✅ ENVIRONMENT=production
- [ ] ✅ HTTPS enabled with valid certificate
- [ ] ✅ All tests passing
- [ ] ✅ No hardcoded secrets in code
- [ ] ✅ Database backups enabled
- [ ] ✅ Error logging configured
- [ ] ✅ Security headers verified
- [ ] ✅ Rate limiting enabled
- [ ] ✅ CSRF protection enabled
- [ ] ✅ Audit logging working
- [ ] ✅ Dependencies updated
- [ ] ✅ Code review completed
- [ ] ✅ Security scan passed

---

## Rollback Plan

If critical issues discovered in production:

```bash
# 1. Stop application
systemctl stop agroai

# 2. Revert to previous version
git checkout <previous-commit>
pip install -r requirements.txt

# 3. Restart
systemctl start agroai

# 4. Notify team
# Create incident report
```

---

## Additional Resources

- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

---

## Support

For questions or issues during remediation:

1. Review the full SECURITY-REVIEW.md for detailed context
2. Check test results for specific failures
3. Consult OWASP resources for best practices
4. Create GitHub issues for each vulnerability
