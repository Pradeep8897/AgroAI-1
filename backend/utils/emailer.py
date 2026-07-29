import os
import smtplib
import time
import requests
from email.message import EmailMessage
from typing import Optional


def _build_reset_message(to_email: str, reset_url: str, subject: str = "AgroAI Password Reset") -> EmailMessage:
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.environ.get('SMTP_FROM') or os.environ.get('SMTP_USER') or 'no-reply@agroai.local'
    msg['To'] = to_email
    text = (
        f"You requested a password reset for your AgroAI account.\n\n"
        f"Click the link below to reset your password (valid for 30 minutes):\n\n{reset_url}\n\n"
        "If you did not request this, ignore this email."
    )
    html = (
        f"<p>You requested a password reset for your AgroAI account.</p>"
        f"<p>Click the link below to reset your password (valid for 30 minutes):</p>"
        f"<p><a href=\"{reset_url}\">Reset Password</a></p>"
        f"<p>If you did not request this, ignore this email.</p>"
    )
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')
    return msg


def _send_via_smtp(msg: EmailMessage, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, use_tls: bool = True) -> bool:
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP send error: {e}")
        return False


def _send_via_sendgrid(to_email: str, reset_url: str, subject: str = "AgroAI Password Reset") -> bool:
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        return False
    from_email = os.environ.get('SMTP_FROM') or os.environ.get('SENDGRID_FROM') or 'no-reply@agroai.local'
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": f"Reset your password: {reset_url}"},
            {"type": "text/html", "value": f"<a href=\"{reset_url}\">Reset Password</a>"}
        ]
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    try:
        resp = requests.post('https://api.sendgrid.com/v3/mail/send', json=data, headers=headers, timeout=10)
        if resp.status_code in (200, 202):
            return True
        print(f"SendGrid send failed: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False


def send_reset_email(to_email: str, reset_url: str, subject: str = "AgroAI Password Reset", max_retries: int = 3) -> bool:
    """Send a password reset email with retries and fallbacks.

    Order of attempts:
    1. SMTP (if configured)
    2. SendGrid API (if `SENDGRID_API_KEY` present)

    Returns True on success.
    """
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    smtp_use_tls = os.environ.get('SMTP_USE_TLS', '1') == '1'

    # Build the message
    msg = _build_reset_message(to_email, reset_url, subject)

    # Attempt SMTP if configured
    if smtp_host and (smtp_user or smtp_pass):
        attempt = 0
        backoff = 1.0
        while attempt < max_retries:
            if _send_via_smtp(msg, smtp_host, smtp_port, smtp_user, smtp_pass, use_tls=smtp_use_tls):
                return True
            attempt += 1
            time.sleep(backoff)
            backoff *= 2
        print("SMTP delivery failed after retries.")

    # Fallback to SendGrid if available
    if os.environ.get('SENDGRID_API_KEY'):
        if _send_via_sendgrid(to_email, reset_url, subject):
            return True

    # Could add AWS SES or other providers here

    print("All email providers failed or are not configured.")
    return False
