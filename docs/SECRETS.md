# Required Repository Secrets and Environment Variables

This project requires a few repository secrets and environment variables for production and CI. Add them in GitHub Settings → Secrets (Repository) or your deployment platform's secret store.

Critical (must be set before deploying or merging):

- `JWT_SECRET_KEY` — Secret used to sign JWT tokens. Required for authentication and MUST be kept secret.

Optional but recommended for email functionality:

- `SMTP_HOST` — SMTP server hostname (e.g., `smtp.sendgrid.net`).
- `SMTP_PORT` — SMTP port number (default `587`).
- `SMTP_USER` — SMTP username.
- `SMTP_PASS` — SMTP password/API key.
- `SMTP_FROM` — Optional: From address used in emails (defaults to `SMTP_USER`).
- `SMTP_USE_TLS` — Optional flag; set to `1` to enable STARTTLS (default `1`).

Alternative providers supported by the app:

- `SENDGRID_API_KEY` — If present, the app can fall back to SendGrid's Web API when SMTP fails or is not configured. Set `SENDGRID_FROM` to override the From header if needed.
- AWS SES: currently supported conceptually (not auto-configured). If you prefer SES, add SES integration in deployment and provide AWS credentials via your platform's IAM roles or environment variables.

Local testing guidance:

1. For local E2E tests you can set a short-lived secret via your shell:

```powershell
$env:JWT_SECRET_KEY='test-secret'
$env:DEV_SEND_RESET_TOKEN='1'
.venv\Scripts\python.exe -m flask run
```

2. On CI (GitHub Actions) add `JWT_SECRET_KEY` as a repository secret. The CI workflow will fail early if this secret is not present.

Security notes:

- Never commit secret values to the repository. Use the GitHub Secrets UI or a secrets manager.
- Rotate `JWT_SECRET_KEY` if you suspect it has been leaked. Expire active tokens as needed.

That's it — add these to your repo secrets and the CI workflow will validate their presence.
