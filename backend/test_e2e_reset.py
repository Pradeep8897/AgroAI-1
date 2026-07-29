import requests
import time
import sys

BASE = 'http://127.0.0.1:5000'

def wait_for_up(timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(BASE + '/api/health', timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

if not wait_for_up(20):
    print('Server did not start within timeout', file=sys.stderr)
    sys.exit(2)

email = 'e2e_test@example.com'
register_payload = {'username': 'e2e_test', 'email': email, 'password': 'InitialPass123!'}

print('Registering test user...')
try:
    r = requests.post(BASE + '/api/auth/register', json=register_payload, timeout=5)
    print('register:', r.status_code, r.text)
except Exception as e:
    print('register exception', e)

print('Requesting password reset...')
try:
    r = requests.post(BASE + '/api/auth/forgot-password', json={'email': email}, timeout=5)
    print('forgot-password:', r.status_code, r.text)
    data = r.json()
    token = data.get('reset_token')
    if not token:
        print('No reset token returned; response:', data)
        sys.exit(3)
    print('Received reset token (dev):', token)
except Exception as e:
    print('forgot-password exception', e)
    sys.exit(4)

print('Calling reset-password with token...')
try:
    r = requests.post(BASE + '/api/auth/reset-password', json={'token': token, 'password': 'NewPass!234'}, timeout=5)
    print('reset-password:', r.status_code, r.text)
except Exception as e:
    print('reset-password exception', e)
    sys.exit(5)

print('Logging in with new password...')
try:
    r = requests.post(BASE + '/api/auth/login', json={'email': email, 'password': 'NewPass!234'}, timeout=5)
    print('login:', r.status_code, r.text)
    if r.status_code == 200:
        print('E2E reset flow: SUCCESS')
    else:
        print('E2E reset flow: FAILED')
except Exception as e:
    print('login exception', e)
    sys.exit(6)
