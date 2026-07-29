---
title: "FINDING-001: Missing Authentication on admin endpoint /api/admin/stats"
labels: [security, critical, backend]
---

**Severity:** CRITICAL

**Location:** `GET /api/admin/stats` (file: `backend/routes/admin.py`)

**Description:** The admin statistics endpoint is accessible without authentication. This exposes sensitive operational and business data to unauthenticated users.

**Impact:** Data disclosure, leakage of business metrics, possible use in targeted attacks.

**Proof / Reproduction:**
- Send an unauthenticated GET request to `/api/admin/stats` and observe a 200 response with metrics payload.

**Remediation:**
- Require authentication and verify the caller's role includes `admin` for this endpoint. Use the existing `require_auth(allowed_roles=[...])` decorator or equivalent authorization middleware.
- Add unit tests to assert 401/403 responses for unauthenticated and unauthorized requests.

**Suggested fix (example):**
```py
@bp.route('/api/admin/stats')
@require_auth(allowed_roles=['admin'])
def admin_stats():
    ...
```

**References:** Security findings workbook `security-reports/AgroAI-Security-Assessment.xlsx` (sheet: Security Findings)

**Notes / Next steps:** Create PR that adds authorization and tests; consider rate-limiting for admin endpoints.
