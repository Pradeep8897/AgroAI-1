# Backend Security Verification Report

## Scope
Verified the AgroAI backend running at `http://127.0.0.1:5000`.
Covered:
- JWT
- Authentication
- Authorization
- RBAC
- IDOR
- SQL Injection
- Command Injection
- Rate limiting
- File upload validation
- CORS
- Security headers
- Secret management
- Every API endpoint exposed by backend routes

## Methodology
1. Started the Flask backend from `backend/app.py`.
2. Executed a live verification script against key endpoints.
3. Inspected source code for authentication, SQL access, file upload, CORS, and secret handling.

## Verified Endpoints
- `GET /api/health` — PASS
- `GET /` — PASS
- `POST /api/auth/register` — PASS
- `POST /api/auth/login` — PASS
- `GET /api/auth/profile` — PASS when authorized, FAIL without token
- `POST /api/admin/login` — PASS (but insecure fixed admin credentials)
- `GET /api/admin/stats` — PASS for admin token, FAIL for user token
- `GET /api/equipment` — PASS
- `GET /api/products` — PASS
- `GET /api/market/prices?crop=Tomato` — PASS
- `GET /api/market/mandis?pincode=400001` — PASS
- `POST /api/assistant/chat` — PASS
- `POST /api/profit/optimize` — PASS
- `GET /api/listings` — PASS
- `POST /api/products/order` — PASS, but no auth required (security issue)
- `GET /api/notifications?user_id=1` — PASS, no auth required (security issue)
- `GET /api/uploads/<filename>` — 404 on a missing file, no auth required
- `POST /api/db/init` — PASS, no auth required (security issue)

## Findings

### JWT
- Verified JWT token generation and validation via `/api/auth/login` and `/api/auth/profile`.
- `Authorization: Bearer <token>` works correctly.
- Token expiration handling is provided by `jwt.decode`.
- Issue: `JWT_SECRET_KEY` has an insecure default value in `backend/utils/jwt_handler.py`.

Status: PARTIAL PASS

### Authentication
- User registration and login are functional.
- Authentication is enforced on protected routes using `@require_auth`.
- Admin login uses hard-coded credentials `admin/admin123`, which is insecure and should be removed or replaced.

Status: PARTIAL PASS

### Authorization
- Enforced on protected endpoints such as `/api/auth/profile`, `/api/admin/stats`, `/api/crop/recommend`, `/api/disease/detect`, `/api/equipment/book`, `/api/products/orders`, and `/api/crop/history`.
- Admin-only access works for `/api/admin/stats`.
- However, several endpoints that should likely require authentication are public.

Status: PARTIAL FAIL

### RBAC
- Role-based access works for admin-only endpoint `/api/admin/stats`.
- General allowed_roles enforcement is present in `utils/jwt_handler.py`.
- No further fine-grained RBAC checks observed beyond the decorator.

Status: PASS for implemented RBAC checks, but limited coverage.

### IDOR (Insecure Direct Object Reference)
- `POST /api/products/order` accepts `user_id` from request body without authorization.
  - Verified live: order can be created without token and arbitrary `user_id`.
- `GET /api/notifications?user_id=1` is accessible without auth.

Status: FAIL

### SQL Injection
- Most database queries use parameterized placeholders (`?` for SQLite, `%s` for MySQL).
- `get_listings` builds filter queries safely using parameterized placeholders.
- No raw concatenation of untrusted SQL input was found in inspected routes.

Status: PASS

### Command Injection
- No `subprocess`, `Popen`, or shell execution usage was found in backend source.

Status: PASS

### Rate limiting
- No rate limiting or request throttling was found in the backend.
- Endpoints such as login, admin login, and public queries are not protected from brute force or abuse.

Status: FAIL

### File upload validation
- `POST /api/disease/detect` uses `secure_filename()` and saves files to the upload folder.
- No validation is performed on file extension, file type, or file size.
- Public file retrieval via `/api/uploads/<filename>` is accessible without auth.

Status: FAIL

### CORS
- `CORS(app, resources={r"/api/*": {"origins": "*"}})` is configured.
- This allows any origin to access API resources and is overly permissive.

Status: FAIL

### Security headers
- No security headers are configured in the Flask app.
- Missing headers include Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Strict-Transport-Security.

Status: FAIL

### Secret management
- `JWT_SECRET_KEY` defaults to a weak development value.
- Database credentials default to `root` / blank and database selection is controlled by env variables.
- No secure secrets store or runtime secret vault is used.

Status: FAIL

## Endpoint Authorization Summary
| Endpoint | Auth Required | Notes |
|---|---|---|
| `GET /api/health` | No | Health check should remain public. |
| `GET /` | No | App root. |
| `POST /api/auth/register` | No | Expected public. |
| `POST /api/auth/login` | No | Expected public. |
| `GET /api/auth/profile` | Yes | Verified. |
| `POST /api/admin/login` | No | Expected public, but insecure credentials. |
| `GET /api/admin/stats` | Yes | Verified admin-only. |
| `GET /api/equipment` | No | Public catalog. |
| `POST /api/equipment` | No | Public creation; should likely require auth. |
| `POST /api/equipment/book` | Yes | Verified. |
| `GET /api/equipment/history` | Yes | Verified. |
| `GET /api/products` | No | Public product catalog. |
| `POST /api/products/order` | No | Security issue; should require auth. |
| `GET /api/products/orders` | Yes | Verified. |
| `GET /api/listings` | No | Public listing search. |
| `POST /api/listings` | Yes | Verified. |
| `GET /api/uploads/<filename>` | No | Public file access. |
| `POST /api/db/init` | No | Dangerous open initialization endpoint. |
| `POST /api/crop/recommend` | Yes | Verified. |
| `POST /api/crop/fertilizer` | No | Public. |
| `POST /api/crop/calendar` | No | Public. |
| `GET /api/crop/history` | Yes | Verified. |
| `POST /api/disease/detect` | Yes | Verified. |
| `GET /api/disease/reports` | Yes | Verified. |
| `GET /api/market/prices` | No | Public market data. |
| `POST /api/market/predict` | No | Public prediction endpoint. |
| `GET /api/market/mandis` | No | Public. |
| `POST /api/assistant/chat` | No | Public chat. |
| `POST /api/profit/optimize` | No | Public profit calculator. |
| `GET /api/notifications` | No | Security issue. |

## Critical Issues
1. `POST /api/products/order` can be used without authentication and accepts arbitrary `user_id`.
2. `GET /api/notifications` can be accessed without authorization.
3. `POST /api/db/init` is publicly accessible and can reinitialize/seed the database.
4. Admin login uses fixed credentials `admin/admin123`.
5. CORS is configured with wildcard origin `*`.
6. No rate limiting is implemented.
7. Upload handling lacks file type and size validation.
8. Insecure default secret `JWT_SECRET_KEY` and weak default DB config.
9. No security headers are configured.

## Recommendations
- Restrict `POST /api/products/order` to authenticated users and derive `user_id` from JWT.
- Protect `/api/notifications` and similar user-specific endpoints with authentication.
- Remove or protect `/api/db/init` behind admin-only access or disable it in production.
- Replace hard-coded admin credentials with a secure admin user store or environment-managed credentials.
- Add rate limiting using Flask-Limiter or a gateway.
- Tighten CORS to allowed frontend origins only.
- Add security headers via Flask-Talisman or custom response middleware.
- Enforce upload file validation: allowed MIME types, extensions, max size, and virus scanning if possible.
- Require `JWT_SECRET_KEY` and DB credentials from environment securely; remove insecure defaults.

## Conclusion
The backend authentication and JWT validation are functional, but the application currently has several serious security issues in authorization, public endpoint exposure, file upload validation, CORS, rate limiting, and secret management.

A follow-up remediation sprint is required before this backend is safe for production.
