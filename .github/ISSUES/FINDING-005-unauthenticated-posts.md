---
title: "FINDING-005: Unauthenticated POST endpoints"
labels: [security, high, backend]
---

**Severity:** HIGH

**Location:** Multiple POST endpoints: `/api/admin/login`, `/api/assistant/chat`, `/api/crop/calendar`, `/api/crop/fertilizer`, `/api/market/predict`, `/api/profit/optimize` (see `Vulnerability Test Results/findings.xlsx`)

**Description:** Several state-changing endpoints accept POST requests without authentication. This allows unauthenticated actors to create or modify data.

**Impact:** Attackers can create bookings, manipulate crop/market predictions, or submit fraudulent data.

**Proof / Reproduction:**
- Send an unauthenticated POST request to the listed endpoints and observe success responses or creation of resources.

**Remediation:**
- Require authentication on all state-changing endpoints (`POST`, `PUT`, `DELETE`). Apply `@require_auth(allowed_roles=[...])` with appropriate role restrictions.
- Add automated tests asserting 401/403 for unauthenticated requests.

**Suggested fix (example):**
```py
@bp.route('/api/crop/calendar', methods=['POST'])
@require_auth(allowed_roles=['user','farmer','expert','admin'])
def add_calendar():
    ...
```

**Notes / Next steps:** Perform a scan to identify other unauthenticated state-changing endpoints and harden them.
