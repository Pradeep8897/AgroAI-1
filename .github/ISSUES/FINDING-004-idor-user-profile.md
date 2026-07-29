---
title: "FINDING-004: IDOR on user profile endpoint"
labels: [security, critical, backend]
---

**Severity:** CRITICAL

**Location:** `GET /api/auth/profile` (file: `backend/routes/auth.py`)

**Description:** The user profile endpoint accepts a user_id parameter from the request and returns profile data without verifying that the requester is authorized to access that user_id.

**Impact:** Horizontal privilege escalation; users can access or modify other users' data.

**Proof / Reproduction:**
- Call `/api/auth/profile?user_id=<other_user_id>` while authenticated as a non-admin user and observe returned profile data for the other user.

**Remediation:**
- Derive the `user_id` from the verified JWT token (`request.user_id`) and ignore any supplied query/body `user_id` for profile access. For admin-only operations that must accept an explicit `user_id`, require `admin` role.

**Suggested fix (example):**
```py
@require_auth()
def profile():
    current_user_id = request.user_id
    return user_service.get_profile(current_user_id)
```

**Notes / Next steps:** Add tests for attempted access to other users' profiles and a code review to ensure similar patterns don't exist elsewhere.
