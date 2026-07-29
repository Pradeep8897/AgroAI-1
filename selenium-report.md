# Selenium E2E Verification Report

## Summary
- Total tests executed: 5
- Passed: 5
- Failed: 0
- Skipped: 0

## Environment
- Operating System: Windows
- Frontend URL: `http://127.0.0.1:5174`
- Backend URL: `http://127.0.0.1:5000`
- ChromeDriver: `118.0.5993.70`
- Selenium WebDriver: `4.46.0`

## Results
1. `login-page-elements` — PASS
2. `empty-form-validation` — PASS
3. `invalid-credentials` — PASS
4. `google-signin-button` — PASS
5. `successful-login` — PASS

## Observations
- The login page is reachable at `http://127.0.0.1:5174/login#/login`.
- The test script correctly sets `agroai_backend_url` in localStorage and refreshes the page so the frontend uses the local backend.
- The Google sign-in button is present and detected using a flexible XPath pattern that matches `Continue with Google` or similar visible text.
- No failures occurred, so no failure screenshots were generated.

## Notes
- Run the suite from the `selenium-tests` folder with:
  ```bash
  cd selenium-tests
  npm test
  ```
- Ensure the backend server is running on `http://127.0.0.1:5000` and the frontend is running on `http://127.0.0.1:5174` before execution.
