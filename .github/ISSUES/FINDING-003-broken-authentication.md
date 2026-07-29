---
title: "FINDING-003: Broken Authentication / Predictable JWT tokens"
labels: [security, critical, backend]
---

**Severity:** CRITICAL

**Location:** `backend/routes/auth.py` / `backend/utils/jwt_handler.py`

**Description:** Authentication appears to accept mock or predictable JWT formats. Tokens may be forged or accepted without proper verification.

**Impact:** Privilege escalation, session hijacking, unauthorized access to protected endpoints.

**Proof / Reproduction:**
- Audit `jwt_handler` implementation and confirm that token verification uses a secure secret and a well-tested JWT library such as PyJWT; attempt to craft malformed token and observe acceptance.

**Remediation:**
- Ensure `JWT_SECRET_KEY` is required and documented (CI already checks for its presence). Use `PyJWT` for signing/verification with secure algorithms (e.g., `HS256`), validate `exp`, `iat`, `aud`/`iss` claims as appropriate.
- Add automated tests for token verification and rejection of malformed/expired tokens.

**Suggested fix (example):**
```py
import jwt
payload = jwt.decode(token, secret, algorithms=['HS256'], options={'require': ['exp','iat']})
```

**Notes / Next steps:** Rotate any compromised JWT secrets and ensure all environments have securely stored `JWT_SECRET_KEY`.
