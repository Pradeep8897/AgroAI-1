Adds CI validation for `JWT_SECRET_KEY` and `docs/SECRETS.md`.

This change:
- Adds a `secrets-validation` job to `.github/workflows/security-review.yml` that fails early if `JWT_SECRET_KEY` is not set.
- Warns when SMTP secrets (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`) are missing.
- Documents required secrets and local test commands in `docs/SECRETS.md`.

Why: prevent accidental merges/deploys without required production secrets and provide clear developer instructions.

Usage:
1. Push branch to remote:

```powershell
git push --set-upstream origin feature/add-secrets-doc-and-ci-checks
```

2. Create PR with GitHub CLI (if installed):

```powershell
gh pr create --title "ci: add secrets validation job + docs" --body-file PR_BODY.md --base main
```

Or open the compare URL in your browser to create the PR manually:

https://github.com/Pradeep8897/AgroAI/compare/feature/add-secrets-doc-and-ci-checks?expand=1
