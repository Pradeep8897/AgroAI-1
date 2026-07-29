import sys
import requests
import json

def run_tests(base_url):
    # Normalize base_url (remove trailing slashes)
    base_url = base_url.strip().rstrip('/')
    print(f"\n=========================================================")
    # Format url cleanly
    print(f"Testing AgroAI Deployed Backend: {base_url}")
    print(f"=========================================================\n")

    session = requests.Session()
    
    # Track passes and fails
    passed = 0
    failed = 0

    def report_result(name, success, info=""):
        nonlocal passed, failed
        status = "PASS" if success else "FAIL"
        symbol = "[+]" if success else "[-]"
        print(f"{symbol} {name:<45} : {status} {info}")
        if success:
            passed += 1
        else:
            failed += 1

    # Test 1: Root endpoint health
    try:
        r = session.get(f"{base_url}/")
        res_json = r.json()
        if r.status_code == 200 and (res_json.get('success') is True or res_json.get('status') == 'success'):
            report_result("Root End-point (GET /)", True, f"({res_json.get('message')})")
        else:
            report_result("Root End-point (GET /)", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        report_result("Root End-point (GET /)", False, str(e))

    # Test 2: Health API health
    try:
        r = session.get(f"{base_url}/api/health")
        if r.status_code == 200 and r.json().get('status') == 'healthy':
            report_result("Health Check (GET /api/health)", True, f"Status: {r.json().get('status')}")
        else:
            report_result("Health Check (GET /api/health)", False, f"Status: {r.status_code}")
    except Exception as e:
        report_result("Health Check (GET /api/health)", False, str(e))

    # Test 3: Initialize Database (sets up schemas on MySQL)
    try:
        r = session.post(f"{base_url}/api/db/init")
        if r.status_code == 200 and r.json().get('success') is True:
            report_result("Initialize Database (POST /api/db/init)", True, f"Message: {r.json().get('message')}")
        else:
            report_result("Initialize Database (POST /api/db/init)", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        report_result("Initialize Database (POST /api/db/init)", False, str(e))

    # Test 4: User Registration
    test_user = {
        "username": "deployment_test",
        "email": "deploytest@agroai.com",
        "password": "securepassword123",
        "role": "farmer"
    }
    # Clean up or check: Since we just initialized, user shouldn't exist. Let's register.
    try:
        r = session.post(f"{base_url}/api/auth/register", json=test_user)
        if r.status_code in [201, 400]: # 201 created or 400 (if already registered)
            success = r.json().get('success') or "already registered" in r.json().get('message', '').lower()
            report_result("User Registration (POST /api/auth/register)", success, f"Message: {r.json().get('message')}")
        else:
            report_result("User Registration (POST /api/auth/register)", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        report_result("User Registration (POST /api/auth/register)", False, str(e))

    # Test 5: User Login
    token = None
    user_id = None
    try:
        r = session.post(f"{base_url}/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        if r.status_code == 200 and r.json().get('success') is True:
            token = r.json().get('token')
            user_id = r.json().get('user', {}).get('id')
            report_result("User Login (POST /api/auth/login)", True, f"Token: {token[:20]}...")
        else:
            report_result("User Login (POST /api/auth/login)", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        report_result("User Login (POST /api/auth/login)", False, str(e))

    # Test 6: User Profile Retrieval
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = session.get(f"{base_url}/api/auth/profile", headers=headers)
            if r.status_code == 200 and r.json().get('success') is True:
                report_result("Get Profile (GET /api/auth/profile)", True, f"Username: {r.json().get('user', {}).get('username')}")
            else:
                report_result("Get Profile (GET /api/auth/profile)", False, f"Status: {r.status_code}, Body: {r.text}")
        except Exception as e:
            report_result("Get Profile (GET /api/auth/profile)", False, str(e))
    else:
        report_result("Get Profile (GET /api/auth/profile)", False, "Skipped: login failed")

    # Test 7: Crop Recommendation Model
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = session.post(f"{base_url}/api/crop/recommend", json={
            "user_id": user_id or 1,
            "N": 90,
            "P": 42,
            "K": 43,
            "ph": 6.5,
            "temp": 24.6,
            "humidity": 70.2,
            "rainfall": 85.0
        }, headers=headers)
        if r.status_code == 200 and r.json().get('success') is True:
            report_result("Crop Recommend (POST /api/crop/recommend)", True, f"Recommended: {r.json().get('top_recommendation')} (Score: {r.json().get('score')})")
        else:
            report_result("Crop Recommend (POST /api/crop/recommend)", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        report_result("Crop Recommend (POST /api/crop/recommend)", False, str(e))

    # Test 8: Fertilizer Recommendation
    try:
        r = session.post(f"{base_url}/api/crop/fertilizer", json={
            "crop": "Rice",
            "N": 40,
            "P": 30,
            "K": 20
        })
        if r.status_code == 200 and r.json().get('success') is True:
            report_result("Fertilizer Recommend (POST /api/crop/fertilizer)", True, f"Recommendations: {len(r.json().get('recommendations', []))}")
        else:
            report_result("Fertilizer Recommend (POST /api/crop/fertilizer)", False, f"Status: {r.status_code}")
    except Exception as e:
        report_result("Fertilizer Recommend (POST /api/crop/fertilizer)", False, str(e))

    # Test 9: Get Equipment Rental Listings
    try:
        r = session.get(f"{base_url}/api/equipment")
        if r.status_code == 200 and r.json().get('success') is True:
            report_result("List Equipment (GET /api/equipment)", True, f"Total listings: {len(r.json().get('equipment', []))}")
        else:
            report_result("List Equipment (GET /api/equipment)", False, f"Status: {r.status_code}")
    except Exception as e:
        report_result("List Equipment (GET /api/equipment)", False, str(e))

    # Test 10: List Products (Shop Marketplace)
    try:
        r = session.get(f"{base_url}/api/products")
        if r.status_code == 200 and r.json().get('success') is True:
            report_result("List Products (GET /api/products)", True, f"Total products: {len(r.json().get('products', []))}")
        else:
            report_result("List Products (GET /api/products)", False, f"Status: {r.status_code}")
    except Exception as e:
        report_result("List Products (GET /api/products)", False, str(e))

    print(f"\n---------------------------------------------------------")
    print(f"Summary: Passed {passed}/{passed + failed} tests.")
    print(f"---------------------------------------------------------\n")
    return failed == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = input("Enter deployed backend base URL (e.g. https://agroai-backend.onrender.com): ")
    else:
        url = sys.argv[1]
    
    if not url:
        print("Error: No URL provided.")
        sys.exit(1)
        
    success = run_tests(url)
    sys.exit(0 if success else 1)
