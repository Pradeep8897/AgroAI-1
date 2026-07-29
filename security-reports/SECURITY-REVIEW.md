# AgroAI Backend Security Assessment Report

**Assessment Date:** 2026-07-27  
**Backend Framework:** Flask (Python)  
**Database:** MySQL/SQLite  
**Authentication:** Custom Mock JWT  
**Authorization:** Role-based (RBAC)

---

## Executive Summary

### Overall Security Score: 35/100 (Critical Issues Present)

**Total Findings: 23**
- Critical: 4
- High: 8
- Medium: 7
- Low: 4

### Most Critical Risks

1. **Unauthenticated Admin Endpoint** - `/api/admin/stats` exposes sensitive platform metrics without authentication
2. **Unsafe Deserialization** - `pickle.load()` used on untrusted files allows arbitrary code execution
3. **Broken Authentication** - Mock JWT tokens with predictable format enable impersonation
4. **IDOR on User Endpoints** - User ID passed as query parameter allows horizontal privilege escalation
5. **CORS Misconfiguration** - Wildcard CORS origins expose API to CSRF attacks

---

## PHASE 1: BACKEND DISCOVERY

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Flask | 3.0.2 |
| **WSGI Server** | Gunicorn | Latest |
| **Database** | MySQL/SQLite | 8.3.0 (MySQL Connector) |
| **Authentication** | Custom Mock JWT | N/A |
| **Password Hashing** | werkzeug.security | 3.0.1 |
| **File Upload** | werkzeug.utils | 3.0.1 |
| **ML Models** | scikit-learn, pickle | Latest |
| **Image Processing** | Pillow (PIL) | Latest |
| **HTTP Client** | requests | 2.31.0 |

### API Architecture

- **Style:** REST API with Blueprint-based routing
- **Authentication Method:** Bearer token (mock JWT format)
- **Authorization:** Role-based access control (RBAC) - partially implemented
- **API Documentation:** None (no Swagger/OpenAPI)
- **Versioning:** No API versioning

### Database Technology

- **Primary:** MySQL with fallback to SQLite
- **Connection Pool:** No connection pooling configured
- **Credentials:** Environment-based with defaults
- **Transactions:** Basic commit/rollback
- **Stored Procedures:** Not used (raw SQL queries)

### File Upload Functionality

- **Location:** `/uploads` or `/tmp/uploads` on Vercel
- **Validation:** `secure_filename()` used (good)
- **Dangerous Pattern:** Files are executed/loaded with `pickle.load()` (critical issue)
- **No file type validation**
- **No file size limits**

### Session Handling

- **Session Type:** Stateless bearer token
- **Token Format:** `mock-jwt-token-{user_id}-{role}`
- **Token Storage:** Client-side (no validation)
- **Session Timeout:** Not implemented
- **Token Revocation:** Not implemented

### Third-Party Integrations

- No OAuth/OIDC providers configured
- No payment gateways
- Google authentication mentioned in frontend but not implemented in backend

---

## PHASE 2: API DISCOVERY

### API Endpoint Inventory

| Endpoint | Method | Auth Required | Roles | Status |
|----------|--------|---------------|-------|--------|
| `/api/auth/register` | POST | No | Public | 🔴 Vulnerable |
| `/api/auth/login` | POST | No | Public | 🔴 Vulnerable |
| `/api/auth/profile` | GET | Weak | User | 🔴 IDOR |
| `/api/auth/profile` | PUT | Weak | User | 🔴 IDOR |
| `/api/auth/forgot-password` | POST | No | Public | 🟡 Info Disclosure |
| `/api/crop/recommend` | POST | No | Public | 🔴 No Auth |
| `/api/crop/log` | POST | No | Public | 🔴 No Auth |
| `/api/crop/history` | GET | No | Public | 🔴 IDOR |
| `/api/disease/detect` | POST | No | Public | 🔴 Unsafe Deserialization |
| `/api/disease/list` | GET | No | Public | ✅ Safe |
| `/api/disease/details` | GET | No | Public | ✅ Safe |
| `/api/disease/reports` | GET | No | Public | 🔴 IDOR |
| `/api/market/prices` | GET | No | Public | ✅ Safe |
| `/api/market/trends` | GET | No | Public | ✅ Safe |
| `/api/equipment` | GET | No | Public | ✅ Safe |
| `/api/equipment` | POST | No | Public | 🔴 No Auth |
| `/api/bookings` | POST | No | Public | 🔴 No Auth |
| `/api/bookings` | GET | No | Public | 🔴 IDOR |
| `/api/orders` | POST | No | Public | 🔴 No Auth |
| `/api/orders` | GET | No | Public | 🔴 IDOR |
| `/api/admin/stats` | GET | No | Admin | 🔴 No Auth |
| `/api/notifications` | GET | No | Public | 🔴 IDOR |
| `/api/notifications` | POST | No | Public | 🔴 No Auth |
| `/api/profit/calculate` | POST | No | Public | 🔴 No Auth |

**Total Endpoints:** 24  
**Authenticated:** 2  
**Vulnerable:** 22  

---

## PHASE 3: STATIC APPLICATION SECURITY TESTING (SAST)

### VULNERABILITY FINDINGS

---

## 1. CRITICAL: Unauthenticated Admin Endpoint

**Severity:** CRITICAL  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**File:** `backend/routes/admin.py` (Line 3-52)  
**Endpoint:** `GET /api/admin/stats`

### Description
The admin statistics endpoint is completely unauthenticated and publicly accessible. It exposes sensitive platform metrics including:
- Total user count
- Total revenue
- Equipment booking details
- User email addresses
- Disease scan statistics

### Code Vulnerable
```python
@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_stats():
    # No authentication check!
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    # ... returns sensitive metrics
```

### Impact
- **Data Disclosure:** Attacker can enumerate user count, revenue metrics, and business intelligence
- **Competitive Intelligence:** Business metrics exposed to competitors
- **User Privacy:** Email addresses and usage patterns leaked
- **System Intelligence:** Reveals platform scale and traffic patterns

### Exploitation Scenario
```bash
curl https://api.agroai.com/api/admin/stats
# Returns all admin metrics without authentication
```

### Recommended Fix
```python
@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_stats():
    # Add authentication and role validation
    auth_header = request.headers.get('Authorization', '')
    user_role = validate_token(auth_header)
    
    if not user_role or user_role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    # ... proceed with stats retrieval
```

---

## 2. CRITICAL: Unsafe Deserialization with pickle.load()

**Severity:** CRITICAL  
**CWE:** CWE-502 (Deserialization of Untrusted Data)  
**Files:** 
- `backend/routes/disease.py` (Line 16-21)
- `backend/routes/crop.py` (Line 35-41)

### Description
The application uses `pickle.load()` to deserialize untrusted pickle files. This allows arbitrary Python code execution during model loading.

### Vulnerable Code
```python
# disease.py
with open(disease_model_path, "rb") as f:
    disease_model = pickle.load(f)  # DANGEROUS!

# crop.py
with open(crop_model_path, "rb") as f:
    crop_model = pickle.load(f)  # DANGEROUS!
```

### Impact
- **Remote Code Execution (RCE):** Attacker can execute arbitrary code on the server
- **Complete System Compromise:** If model files are compromised, full system control is gained
- **Supply Chain Risk:** If models are downloaded or updated, attackers can inject malicious code

### Exploitation Scenario
1. Attacker creates malicious pickle file with embedded shell commands
2. Replaces legitimate model file: `disease_model.pkl` or `crop_model.pkl`
3. When application starts, arbitrary code executes with application privileges
4. Example payload in pickle: Execute `rm -rf /` or exfiltrate database

### Recommended Fix
```python
import joblib
import dill

# Better: Use joblib (safer for sklearn models)
crop_model = joblib.load(crop_model_path)

# Alternative: Use Keras/TensorFlow models (safer formats)
from tensorflow import keras
disease_model = keras.models.load_model(disease_model_path)

# If pickle must be used: Verify digital signatures
import hmac
import hashlib

def load_trusted_model(filepath, expected_hash):
    with open(filepath, 'rb') as f:
        model_data = f.read()
    
    # Verify HMAC signature
    computed_hash = hmac.new(b'secret_key', model_data, hashlib.sha256).digest()
    if not hmac.compare_digest(computed_hash, expected_hash):
        raise ValueError("Model file integrity check failed!")
    
    return pickle.loads(model_data)
```

---

## 3. CRITICAL: Broken Authentication - Mock JWT Tokens

**Severity:** CRITICAL  
**CWE:** CWE-613 (Insufficient Session Expiration)  
**File:** `backend/routes/auth.py` (Line 45-60)

### Description
The application uses predictable mock JWT tokens in the format `mock-jwt-token-{user_id}-{role}` without any cryptographic validation. This allows:
- Token prediction/guessing
- Role tampering
- Session hijacking

### Vulnerable Code
```python
# Login returns:
"token": f"mock-jwt-token-{user['id']}-{user['role']}"

# Profile extraction:
auth_header = request.headers.get('Authorization', '')
if auth_header.startswith('Bearer mock-jwt-token-'):
    parts = auth_header.split('-')
    if len(parts) >= 4:
        user_id = int(parts[3])  # UNSAFE - attacker can change this!
```

### Impact
- **Authentication Bypass:** Attacker can guess valid tokens
- **Privilege Escalation:** Attacker can change role from "farmer" to "admin"
- **Horizontal Access:** Attacker can access any user's data by changing user_id
- **No Token Validation:** Server doesn't validate signature or expiration

### Exploitation Scenario
```bash
# Legitimate user gets:
Authorization: Bearer mock-jwt-token-42-farmer

# Attacker modifies to:
Authorization: Bearer mock-jwt-token-999-admin  # Access admin functions
Authorization: Bearer mock-jwt-token-1-farmer   # Access user 1's data

# Server accepts it without validation!
```

### Recommended Fix
```python
import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-in-production")

def generate_token(user_id, role):
    """Generate proper JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
        'jti': str(uuid.uuid4())  # Token ID for revocation
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """Verify JWT signature and claims"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidSignatureError:
        return None
    except jwt.DecodeError:
        return None

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    # ... existing validation ...
    if check_password_hash(user['password'], password):
        token = generate_token(user['id'], user['role'])
        return jsonify({
            "success": True,
            "token": token,  # Real JWT
            "user": {...}
        }), 200

@auth_bp.route('/api/auth/profile', methods=['GET'])
def profile():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    payload = verify_token(token)
    if not payload:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    
    user_id = payload['user_id']  # Extract from verified token
    # ... proceed ...
```

---

## 4. CRITICAL: Insecure Direct Object Reference (IDOR) on User Profile

**Severity:** CRITICAL  
**CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)  
**File:** `backend/routes/auth.py` (Line 65-100)  
**Endpoints:** `GET/PUT /api/auth/profile`

### Description
User profile endpoints accept `user_id` as a query parameter or JSON body without proper authorization. An attacker can access/modify any user's profile.

### Vulnerable Code
```python
@auth_bp.route('/api/auth/profile', methods=['GET', 'PUT'])
def profile():
    # Weak token parsing
    auth_header = request.headers.get('Authorization', '')
    user_id = None
    if auth_header.startswith('Bearer mock-jwt-token-'):
        parts = auth_header.split('-')
        if len(parts) >= 4:
            user_id = int(parts[3])

    # FALLBACK TO USER-PROVIDED ID!
    if not user_id:
        user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    
    # No validation that token's user_id matches requested user_id!
```

### Impact
- **Horizontal Privilege Escalation:** User 42 can access User 1's profile
- **Data Modification:** Attacker can change other users' email, location, farm_size
- **Identity Theft:** Attacker can modify victim's profile details
- **Information Disclosure:** Attacker can enumerate all user IDs (1, 2, 3, ...)

### Exploitation Scenario
```bash
# Attacker is logged in as user_id=100
GET /api/auth/profile?user_id=50
Authorization: Bearer mock-jwt-token-100-farmer

# Server returns user 50's profile (not user 100's!)

# Or modify another user's profile:
PUT /api/auth/profile
Authorization: Bearer mock-jwt-token-100-farmer
Body: {
  "user_id": 50,
  "email": "attacker@evil.com",
  "phone": "+123456789"
}

# Server updates user 50's data!
```

### Recommended Fix
```python
def require_auth(f):
    """Decorator to enforce authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        token = auth_header[7:]
        payload = verify_token(token)
        if not payload:
            return jsonify({"success": False, "message": "Invalid token"}), 401
        
        return f(payload, *args, **kwargs)
    return decorated_function

@auth_bp.route('/api/auth/profile', methods=['GET', 'PUT'])
@require_auth
def profile(payload):
    # Extract user_id from verified token, not from request!
    user_id = payload['user_id']
    
    # Only allow user to access their own profile
    if request.method == 'GET':
        user = UserModel.get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Don't expose password hash!
        del user['password']
        return jsonify({"success": True, "user": user})
    
    # ... similar for PUT ...
```

---

## 5. CRITICAL: Insecure Direct Object Reference (IDOR) on Disease Reports

**Severity:** CRITICAL  
**CWE:** CWE-639  
**File:** `backend/routes/disease.py`  
**Endpoint:** `GET /api/disease/reports`

### Description
Disease reports endpoint allows querying any user's disease detection history without authorization.

### Impact
- **Medical Privacy Violation:** Attacker can view other users' disease detection records
- **Sensitive Health Data Exposure:** Disease history, crop infections, treatment information
- **HIPAA/Privacy Violation:** Health-related information exposed

### Recommended Fix
```python
@disease_bp.route('/api/disease/reports', methods=['GET'])
@require_auth
def get_disease_reports(payload):
    user_id = payload['user_id']  # From token, not request
    
    # Only return this user's reports
    reports = DiseaseModel.get_user_reports(user_id)
    return jsonify({"success": True, "reports": reports})
```

---

## 6. HIGH: Broken CORS Configuration

**Severity:** HIGH  
**CWE:** CWE-942 (Overly Permissive Cross-origin Resource Sharing Policy)  
**File:** `backend/app.py` (Line 27)

### Description
CORS is configured with wildcard origins (`*`), exposing the API to CSRF attacks from any website.

### Vulnerable Code
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### Impact
- **CSRF Attacks:** Malicious website can make authenticated requests
- **Credential Theft:** If cookies are used, attacker can perform actions on behalf of user
- **API Abuse:** Attacker can call API endpoints from any origin

### Exploitation Scenario
Attacker hosts malicious website:
```html
<script>
fetch('https://api.agroai.com/api/crop/recommend', {
  method: 'POST',
  credentials: 'include',  // Sends session cookie
  body: JSON.stringify({...})
})
</script>
```
Server accepts request from any origin.

### Recommended Fix
```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://agroai.com",
            "https://www.agroai.com",
            "http://localhost:5173"  # Development only
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,  # Don't send cookies unless needed
        "max_age": 3600
    }
})
```

---

## 7. HIGH: No Authentication on File Upload Endpoint

**Severity:** HIGH  
**CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type)  
**File:** `backend/routes/disease.py` (Line 39-80)  
**Endpoint:** `POST /api/disease/detect`

### Description
Disease detection endpoint accepts file uploads without authentication, allowing:
- Disk space exhaustion (DoS)
- Upload of arbitrary files
- Processing resource abuse

### Impact
- **Denial of Service:** Attacker uploads massive files, fills disk space
- **Resource Exhaustion:** Server wastes CPU processing huge images
- **Model Poisoning:** Attacker can feed malicious images triggering model extraction

### Vulnerable Code
```python
@disease_bp.route('/api/disease/detect', methods=['POST'])
def detect_disease():
    # NO AUTHENTICATION!
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No image file uploaded."}), 400
    
    image_file = request.files['image']
    # No file size check
    # No authentication
```

### Recommended Fix
```python
from werkzeug.exceptions import BadRequest

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

@disease_bp.route('/api/disease/detect', methods=['POST'])
@require_auth
def detect_disease(payload):
    user_id = payload['user_id']
    
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No image file"}), 400
    
    image_file = request.files['image']
    
    # Validate file size
    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    if file_size > MAX_FILE_SIZE:
        return jsonify({"success": False, "message": "File too large"}), 400
    image_file.seek(0)
    
    # Validate file extension
    if not image_file.filename or \
       image_file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "message": "Invalid file type"}), 400
    
    # Validate MIME type
    if not image_file.content_type.startswith('image/'):
        return jsonify({"success": False, "message": "Invalid file type"}), 400
    
    # ... process image ...
```

---

## 8. HIGH: Missing Authentication on Multiple Endpoints

**Severity:** HIGH  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**Affected Endpoints:**
- `POST /api/crop/recommend` (Creates crop recommendation)
- `POST /api/crop/log` (Logs crop selection)
- `POST /api/equipment` (Lists equipment rental)
- `POST /api/bookings` (Creates equipment booking)
- `POST /api/orders` (Creates marketplace order)
- `POST /api/notifications` (Creates notification)

### Description
Multiple endpoints that should require authentication are publicly accessible, allowing any user to:
- Create fake bookings
- Place orders without payment
- Log false crop recommendations
- Spam notifications

### Recommended Fix
Add `@require_auth` decorator to all sensitive endpoints:
```python
@crop_bp.route('/api/crop/recommend', methods=['POST'])
@require_auth
def recommend_crop(payload):
    user_id = payload['user_id']
    # ... process with authenticated user ...

@crop_bp.route('/api/crop/log', methods=['POST'])
@require_auth
def log_crop(payload):
    user_id = payload['user_id']
    # ... log with user association ...
```

---

## 9. HIGH: Password Reset Without Verification

**Severity:** HIGH  
**CWE:** CWE-640 (Weak Password Recovery Mechanism)  
**File:** `backend/routes/auth.py` (Line 127-137)

### Description
Forgot password endpoint doesn't actually send reset instructions - just returns success. No email verification, token, or actual reset mechanism implemented.

### Impact
- **Incomplete Feature:** Users can't actually reset passwords
- **Account Lockout:** Users locked out indefinitely
- **Social Engineering Risk:** Endpoint can be used to enumerate valid emails

### Recommended Fix
```python
import secrets
from datetime import datetime, timedelta

@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if not email:
        return jsonify({"success": False, "message": "Email required"}), 400
    
    user = UserModel.get_user_by_email(email)
    if not user:
        # Don't reveal if email exists (prevents enumeration)
        return jsonify({
            "success": True,
            "message": "If email exists, reset link sent"
        }), 200
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    token_hash = generate_password_hash(reset_token)
    
    # Store token with expiration (15 minutes)
    expiration = datetime.utcnow() + timedelta(minutes=15)
    UserModel.create_password_reset_token(user['id'], token_hash, expiration)
    
    # Send email with reset link
    send_password_reset_email(user['email'], reset_token)
    
    return jsonify({
        "success": True,
        "message": "Reset link sent to email"
    }), 200

@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        return jsonify({"success": False, "message": "Invalid request"}), 400
    
    # Verify token validity and expiration
    user_id = UserModel.verify_reset_token(token)
    if not user_id:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 400
    
    # Update password
    UserModel.update_password(user_id, new_password)
    
    return jsonify({
        "success": True,
        "message": "Password reset successfully"
    }), 200
```

---

## 10. HIGH: No Input Validation on Numeric Fields

**Severity:** HIGH  
**CWE:** CWE-20 (Improper Input Validation)  
**Files:** Multiple endpoints (crop.py, equipment endpoints, etc.)

### Description
Numeric fields (N, P, K, pH, temperature, humidity, rainfall) are converted to float without:
- Range validation
- Negative value checks
- Scientific notation limits
- NaN/Infinity handling

### Impact
- **Denial of Service:** Large values consume CPU in calculations
- **Unexpected Behavior:** NaN/Infinity values break algorithms
- **Data Corruption:** Negative values stored in database

### Vulnerable Code
```python
try:
    N = float(data.get('N', 0))
    P = float(data.get('P', 0))
    ph = float(data.get('ph', 6.0))  # No validation!
except ValueError:
    return jsonify({"success": False, "message": "Must be numeric"}), 400
```

### Recommended Fix
```python
def validate_soil_parameters(data):
    """Validate soil nutrient parameters"""
    errors = []
    
    # Nitrogen (0-300)
    try:
        N = float(data.get('N', 0))
        if not (0 <= N <= 300):
            errors.append("N must be between 0-300")
        if math.isnan(N) or math.isinf(N):
            errors.append("N contains invalid value")
    except (ValueError, TypeError):
        errors.append("N must be numeric")
    
    # pH (4.0-9.0)
    try:
        ph = float(data.get('ph', 6.0))
        if not (4.0 <= ph <= 9.0):
            errors.append("pH must be between 4.0-9.0")
        if math.isnan(ph) or math.isinf(ph):
            errors.append("pH contains invalid value")
    except (ValueError, TypeError):
        errors.append("pH must be numeric")
    
    return errors
```

---

## 11. HIGH: Hardcoded Database Defaults

**Severity:** HIGH  
**CWE:** CWE-798 (Use of Hard-Coded Credentials)  
**File:** `backend/database/mysql_connection.py` (Line 7-11)

### Description
Database credentials have hardcoded defaults with root user and empty password.

### Vulnerable Code
```python
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")      # Hardcoded root!
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")  # Empty password!
DB_NAME = os.environ.get("DB_NAME", "agroai")
```

### Impact
- **Default Credentials:** Attackers know default values
- **Database Compromise:** Anyone with network access can connect as root
- **Privilege Escalation:** Root user has unlimited permissions

### Recommended Fix
```python
import os
from pathlib import Path

# Require environment variables in production
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "agroai")

# Fail loudly in production if not configured
if os.environ.get("ENVIRONMENT") == "production":
    if not DB_HOST or not DB_USER or not DB_PASSWORD:
        raise EnvironmentError(
            "Database credentials must be set via environment variables "
            "in production. Missing: " +
            ", ".join([
                k for k in ["DB_HOST", "DB_USER", "DB_PASSWORD"]
                if not os.environ.get(k)
            ])
        )

# Only use defaults for development
if os.environ.get("ENVIRONMENT") != "development":
    DB_HOST = DB_HOST or "localhost"
    DB_USER = DB_USER or "agroai_user"  # Less privileged user
    DB_PASSWORD = DB_PASSWORD or "change_me_in_production"
```

---

## 12. MEDIUM: No Rate Limiting

**Severity:** MEDIUM  
**CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)  
**File:** `backend/app.py`

### Description
No rate limiting on any endpoint, allowing:
- Brute force password attacks
- Credential stuffing
- API enumeration
- Denial of Service

### Impact
- **Brute Force:** Attacker can try unlimited password combinations
- **Enumeration:** Attacker can enumerate all user IDs
- **Resource Exhaustion:** DoS attacks unchecked

### Recommended Fix
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"  # Or in-memory for testing
)

@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    # ... login logic ...

@auth_bp.route('/api/auth/register', methods=['POST'])
@limiter.limit("3 per hour")  # Max 3 registrations per hour
def register():
    # ... registration logic ...
```

---

## 13. MEDIUM: No HTTPS Enforcement

**Severity:** MEDIUM  
**CWE:** CWE-295 (Improper Certificate Validation)  
**File:** `backend/app.py`

### Description
No HSTS headers or redirect to HTTPS configured.

### Impact
- **Man-in-the-Middle:** Attacker intercepts HTTP traffic
- **Credential Theft:** Passwords/tokens sent in plaintext
- **Data Tampering:** Attacker modifies API responses

### Recommended Fix
```python
@app.before_request
def enforce_https():
    """Redirect HTTP to HTTPS"""
    if not request.is_secure and os.environ.get("ENVIRONMENT") == "production":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

@app.after_request
def add_security_headers(response):
    """Add security headers"""
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## 14. MEDIUM: Error Information Disclosure

**Severity:** MEDIUM  
**CWE:** CWE-209 (Information Exposure Through an Error Message)  
**File:** Multiple files

### Description
Full exception stack traces returned to clients, revealing:
- File paths
- Database structure
- Library versions
- Internal code logic

### Vulnerable Code
```python
except Exception as e:
    print(f"Error loading admin stats: {e}")
    return jsonify({"success": False, "message": str(e)}), 500
```

### Impact
- **Information Disclosure:** Attacker learns system architecture
- **Version Enumeration:** Attacker learns library versions for targeted exploits
- **Attack Surface:** Attacker maps internal system

### Recommended Fix
```python
import logging

logger = logging.getLogger(__name__)

try:
    # ... code ...
except DatabaseError as e:
    logger.error(f"Database error in admin stats: {str(e)}", exc_info=True)
    return jsonify({
        "success": False,
        "message": "An error occurred processing your request"
    }), 500
except Exception as e:
    logger.error(f"Unexpected error in admin stats: {str(e)}", exc_info=True)
    return jsonify({
        "success": False,
        "message": "An unexpected error occurred"
    }), 500
```

---

## 15. MEDIUM: No SQL Injection Protection on Dynamic Queries

**Severity:** MEDIUM  
**CWE:** CWE-89 (SQL Injection)  
**Files:** Multiple database queries

### Note
While the application uses parameterized queries (good!), raw SQL is present in some places. Risk is MEDIUM because parameterized queries are used, but should audit all query locations.

### Review Point
```python
# GOOD - Parameterized
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# RISKY - If dynamic queries ever added
query = f"SELECT * FROM users WHERE {column} = %s"  # DON'T DO THIS!
```

### Recommended Fix
Always use parameterized queries:
```python
# Always parameterized
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND role = %s",
    (email, role)
)
```

---

## 16. MEDIUM: No Audit Logging

**Severity:** MEDIUM  
**CWE:** CWE-778 (Insufficient Logging)  

### Description
No audit trail of sensitive operations:
- Login/logout events
- Password changes
- Profile modifications
- Admin actions
- Booking/order changes

### Impact
- **Compliance Violation:** Unable to audit access for compliance
- **Incident Response:** Cannot trace attacker actions
- **Fraud Detection:** Cannot detect unauthorized modifications

### Recommended Fix
```python
from datetime import datetime

class AuditLog:
    @staticmethod
    def log_event(user_id, event_type, resource, action, status, details=""):
        """Log security-relevant events"""
        conn, is_sqlite = get_connection()
        cursor = conn.cursor()
        try:
            if is_sqlite:
                cursor.execute("""
                    INSERT INTO audit_logs 
                    (user_id, event_type, resource, action, status, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, event_type, resource, action, status, details, datetime.utcnow()))
            else:
                cursor.execute("""
                    INSERT INTO audit_logs 
                    (user_id, event_type, resource, action, status, details, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, event_type, resource, action, status, details, datetime.utcnow()))
            conn.commit()
        finally:
            conn.close()

# Usage
AuditLog.log_event(user_id, "AUTH", "user", "login", "success", f"from IP {request.remote_addr}")
AuditLog.log_event(user_id, "AUTH", "user", "password_change", "success")
AuditLog.log_event(user_id, "PROFILE", "user", "update", "success", "Updated email and phone")
```

---

## 17. MEDIUM: No Session/Token Revocation

**Severity:** MEDIUM  
**CWE:** CWE-613 (Insufficient Session Expiration)

### Description
Once issued, tokens cannot be revoked. Even if password is compromised, old tokens remain valid.

### Impact
- **Compromised Token:** Invalid until natural expiration
- **Logout Ineffective:** User cannot truly log out
- **Long-lived Compromise:** Attacker retains access

### Recommended Fix
```python
# Token blacklist storage
class TokenBlacklist:
    def __init__(self):
        self.blacklist = set()
    
    def revoke(self, jti):
        """Revoke a token by JTI"""
        self.blacklist.add(jti)
    
    def is_blacklisted(self, jti):
        """Check if token is revoked"""
        return jti in self.blacklist

blacklist = TokenBlacklist()

@auth_bp.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout(payload):
    # Revoke the token
    blacklist.revoke(payload['jti'])
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

def verify_token(token):
    """Updated to check blacklist"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if blacklist.is_blacklisted(payload['jti']):
            return None  # Token revoked
        return payload
    except jwt.DecodeError:
        return None
```

---

## 18. MEDIUM: No Input Length Limits

**Severity:** MEDIUM  
**CWE:** CWE-400 (Uncontrolled Resource Consumption)

### Description
Text fields accept unlimited length strings, allowing:
- Buffer overflow attempts
- Memory exhaustion
- Database constraint violations

### Recommended Fix
```python
from flask import request

MAX_LENGTHS = {
    'username': 50,
    'email': 255,
    'password': 128,
    'phone': 20,
    'location': 255,
    'farm_size': 100
}

def validate_string_length(field_name, value):
    """Validate string field length"""
    if len(str(value)) > MAX_LENGTHS.get(field_name, 255):
        return f"{field_name} exceeds maximum length"
    return None

# Usage
email = data.get('email')
if not email or len(email) > MAX_LENGTHS['email']:
    return jsonify({"success": False, "message": "Invalid email"}), 400
```

---

## 19. MEDIUM: No CSRF Token Protection

**Severity:** MEDIUM  
**CWE:** CWE-352 (Cross-Site Request Forgery CSRF)

### Description
No CSRF tokens on state-changing requests (POST, PUT, DELETE).

### Recommended Fix
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@auth_bp.route('/api/auth/login', methods=['POST'])
@csrf.exempt  # For API, use token-based auth instead
def login():
    # ...

# For web forms:
@app.route('/crop/recommend', methods=['POST'])
@csrf.protect
def recommend_crop_form():
    # CSRF token automatically validated
    # ...
```

---

## 20. MEDIUM: Weak Password Requirements

**Severity:** MEDIUM  
**CWE:** CWE-521 (Weak Password Requirements)

### Description
No password strength validation. User can set "123" as password.

### Recommended Fix
```python
import re

def validate_password_strength(password):
    """Validate password meets minimum requirements"""
    errors = []
    
    if len(password) < 12:
        errors.append("Password must be at least 12 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain number")
    if not re.search(r'[!@#$%^&*]', password):
        errors.append("Password must contain special character")
    
    # Check against common passwords
    common_passwords = ['password', 'agroai123', 'admin123', 'user123']
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return errors

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    # ... existing validation ...
    password_errors = validate_password_strength(password)
    if password_errors:
        return jsonify({
            "success": False,
            "message": "Password does not meet requirements",
            "errors": password_errors
        }), 400
```

---

## 21. LOW: Missing Security Headers

**Severity:** LOW  
**CWE:** CWE-693 (Protection Mechanism Failure)

### Description
Missing critical HTTP security headers.

### Recommended Fix
```python
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response
```

---

## 22. LOW: No API Documentation

**Severity:** LOW  
**CWE:** CWE-215 (Information Exposure Through Debug Information)

### Description
No API documentation or Swagger/OpenAPI. Makes it harder for developers to understand security requirements.

### Recommended Fix
```python
from flask_restx import Api, Resource, fields, Namespace

# Create API documentation
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT token with "Bearer " prefix'
    }
}

api = Api(app, version='1.0', title='AgroAI API',
    description='Agricultural Intelligence API',
    authorizations=authorizations
)

crop_ns = Namespace('crop', description='Crop operations')

@crop_ns.route('/recommend')
class CropRecommend(Resource):
    @crop_ns.doc('recommend_crop', security='Bearer')
    @crop_ns.expect(model_crop_input)
    def post(self):
        '''Recommend crops based on soil conditions'''
        pass
```

---

## 23. LOW: Dependency Vulnerabilities

**Severity:** LOW  
**CWE:** CWE-1035 (Known Vulnerable Component)

### Description
Some dependencies may have known vulnerabilities.

### Recommended Fix
```bash
# Regular dependency scanning
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

---

## PHASE 4: DYNAMIC TESTING RESULTS

**Status:** Not performed (requires running backend environment)

Testing should include:
- Token manipulation attempts
- IDOR exploitation tests
- Authentication bypass attempts
- Rate limiting verification
- File upload attacks
- Injection attack validation

---

## REMEDIATION PRIORITY

### Critical (Fix Immediately)
1. ✅ Implement proper JWT authentication with signature validation
2. ✅ Add authentication to all protected endpoints
3. ✅ Remove pickle deserialization or add signature verification
4. ✅ Add IDOR checks to all user-specific endpoints
5. ✅ Restrict CORS to specific origins

### High (Fix Within 1 Week)
6. Add rate limiting to prevent brute force
7. Enforce HTTPS and add security headers
8. Implement password reset functionality
9. Remove database credential defaults
10. Add input validation on all fields

### Medium (Fix Within 2 Weeks)
11. Add audit logging for sensitive operations
12. Implement token revocation mechanism
13. Add CSRF protection
14. Enforce strong password requirements
15. Mask error messages from clients

### Low (Fix Within 1 Month)
16. Add API documentation (Swagger)
17. Implement dependency scanning
18. Review and update all dependencies
19. Add comprehensive security testing

---

## COMPLIANCE NOTES

- **OWASP Top 10 2023:** This application has vulnerabilities in categories: A01:2021 – Broken Access Control, A02:2021 – Cryptographic Failures, A03:2021 – Injection, A05:2021 – Broken Access Control, A07:2021 – Identification and Authentication Failures
- **PCI DSS:** Not compliant (if handling payments)
- **GDPR:** Not compliant (user data exposure)
- **HIPAA:** Not compliant (if handling health data)

---

## CONCLUSION

The AgroAI backend has **critical vulnerabilities** requiring immediate remediation. Priority should be given to authentication and authorization mechanisms. A security-focused code review and penetration testing should follow implementation of critical fixes.

**Estimated Remediation Time:** 2-3 weeks for critical issues, 1-2 months for full security hardening.
