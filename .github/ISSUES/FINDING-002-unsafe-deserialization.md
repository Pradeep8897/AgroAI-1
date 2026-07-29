---
title: "FINDING-002: Unsafe Deserialization in disease/crop model loading"
labels: [security, critical, backend]
---

**Severity:** CRITICAL

**Location:** `disease.py`, `crop.py` (uses `pickle.load()` on untrusted files)

**Description:** The codebase uses `pickle.load()` to deserialize model or data files. Pickle deserialization is unsafe for untrusted input and can lead to remote code execution.

**Impact:** Remote code execution, system compromise, arbitrary code execution under the process user.

**Proof / Reproduction:**
- Inspect source for `pickle.load` calls and confirm they operate on uploaded or external files.

**Remediation:**
- Replace `pickle.load()` with `joblib.load()` for model files where appropriate (joblib is safer for models) or use a safe serialization format (JSON, protobuf) with strict schema validation.
- If pickle must be used, restrict inputs to trusted storage and implement cryptographic signatures and verification of files before deserialization.

**Suggested fix (example):**
```py
from joblib import load as joblib_load
model = joblib_load(model_path)
```

**References:** `security-reports/AgroAI-Security-Assessment.xlsx` (Security Findings)

**Notes / Next steps:** Update unit tests, and review any other uses of `pickle` across the repo.
