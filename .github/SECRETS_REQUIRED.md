Repository secrets required for CI and production

Required secrets (add via GitHub Settings → Secrets → Actions):

- `JWT_SECRET_KEY` — a long, random secret used to sign JWTs (required by backend at import time).
- `SMTP_HOST` — SMTP server hostname for production email delivery.
- `SMTP_PORT` — SMTP port (e.g., 587).
- `SMTP_USER` — SMTP username.
- `SMTP_PASS` — SMTP password (store as secret).
- `SENDGRID_API_KEY` — SendGrid API key (optional fallback).
- `SENTRY_DSN` — (optional) Sentry DSN for error monitoring.

Notes:
- The backend raises an error if `JWT_SECRET_KEY` is not set at import time. Add this secret to avoid CI failures when importing `backend.utils.jwt_handler`.
- CI includes a `secrets-validation` job that will fail early if required secrets are missing.
- Do NOT commit secrets to the repository. Use GitHub Secrets UI to add them.

How to add a secret:
1. Go to the repository on GitHub.
2. Click `Settings` → `Secrets` → `Actions` → `New repository secret`.
3. Enter the name (e.g., `JWT_SECRET_KEY`) and the secret value.
4. Save.

After adding secrets, re-run the workflow to verify the `secrets-validation` job passes.
