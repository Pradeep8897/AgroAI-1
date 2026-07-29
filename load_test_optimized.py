"""
Optimized Load Test with JWT Authentication
Pre-registers users, then tests endpoints with reused tokens
"""

import requests
import threading
import time
import json
from collections import defaultdict
from statistics import mean

# Configuration
BASE_URL = "http://127.0.0.1:5000"
CONCURRENT_USERS = 100
TEST_DURATION_SECONDS = 60

# Shared metrics
metrics = {
    'lock': threading.Lock(),
    'requests': 0,
    'successful': 0,
    'failed': 0,
    'response_times': [],
    'endpoint_stats': defaultdict(lambda: {'count': 0, 'times': [], 'errors': 0}),
    'start_time': None,
    'end_time': None
}

# User tokens (populated during setup)
user_tokens = {}
setup_lock = threading.Lock()

def make_request(method, endpoint, data=None, headers=None):
    """Make a single API request and return response time"""
    try:
        start = time.time()
        full_url = f"{BASE_URL}{endpoint}"
        
        if method == 'GET':
            response = requests.get(full_url, headers=headers, timeout=10)
        else:
            response = requests.post(full_url, json=data, headers=headers, timeout=10)
        
        elapsed_ms = (time.time() - start) * 1000
        
        with metrics['lock']:
            metrics['requests'] += 1
            metrics['response_times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['count'] += 1
            metrics['endpoint_stats'][endpoint]['times'].append(elapsed_ms)
            
            if 200 <= response.status_code < 300:
                metrics['successful'] += 1
            else:
                metrics['failed'] += 1
                metrics['endpoint_stats'][endpoint]['errors'] += 1
        
        return elapsed_ms, response.status_code
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        with metrics['lock']:
            metrics['requests'] += 1
            metrics['failed'] += 1
            metrics['response_times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['count'] += 1
            metrics['endpoint_stats'][endpoint]['times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['errors'] += 1
        return elapsed_ms, 'ERROR'

def setup_user(user_id):
    """Register and authenticate a single user"""
    user_email = f"perf_user_{user_id}@agroai.com"
    user_password = f"PerfPass{user_id}!"
    
    # Register
    register_data = {
        "username": f"PerfUser{user_id}",
        "email": user_email,
        "password": user_password,
        "role": "farmer"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=10)
    except:
        pass  # May already exist
    
    # Login to get token
    login_data = {
        "email": user_email,
        "password": user_password
    }
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        if response.status_code in [200, 201]:
            result = response.json()
            token = result.get('token')
            if token:
                with setup_lock:
                    user_tokens[user_id] = token
                return True
    except:
        pass
    
    return False

def worker(user_id):
    """Worker thread - makes requests using pre-authenticated token"""
    token = user_tokens.get(user_id)
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    while time.time() - metrics['start_time'] < TEST_DURATION_SECONDS:
        # Distribute requests across endpoints
        endpoint_choice = int((time.time() * 1000000 + user_id) % 5)
        
        if endpoint_choice == 0:
            # Market prices (GET, unprotected but with auth)
            make_request('GET', '/api/market/prices', headers=headers)
        
        elif endpoint_choice == 1:
            # Market mandis (GET, unprotected but with auth)
            make_request('GET', '/api/market/mandis', headers=headers)
        
        elif endpoint_choice == 2:
            # Disease reports (GET, protected)
            make_request('GET', '/api/disease/reports', headers=headers)
        
        elif endpoint_choice == 3:
            # Crop recommendation (POST, protected)
            crop_data = {
                'N': 50, 'P': 30, 'K': 20, 'ph': 6.5,
                'temperature': 25, 'humidity': 60, 'rainfall': 500
            }
            make_request('POST', '/api/crop/recommend', crop_data, headers)
        
        elif endpoint_choice == 4:
            # User profile (GET, protected)
            make_request('GET', '/api/auth/profile', headers=headers)
        
        # No delay - hammer the server
        time.sleep(0)

def print_results():
    """Print formatted results"""
    metrics['end_time'] = time.time()
    duration = metrics['end_time'] - metrics['start_time']
    
    print("\n" + "="*80)
    print("AGROAI BACKEND - OPTIMIZED LOAD TEST WITH JWT AUTHENTICATION")
    print("="*80)
    
    print(f"\nTest Configuration:")
    print(f"  Concurrent Users: {CONCURRENT_USERS}")
    print(f"  Duration: {TEST_DURATION_SECONDS} seconds")
    print(f"  API Endpoint: {BASE_URL}")
    print(f"  Auth Method: JWT Bearer Token (pre-authenticated)")
    
    print(f"\n📊 OVERALL METRICS:")
    print(f"  Total Requests: {metrics['requests']}")
    success_pct = (metrics['successful']/max(1, metrics['requests'])*100) if metrics['requests'] > 0 else 0
    print(f"  Successful: {metrics['successful']} ({success_pct:.1f}%)")
    print(f"  Failed: {metrics['failed']}")
    print(f"  Actual Duration: {duration:.2f} seconds")
    
    if metrics['response_times'] and metrics['requests'] > 0:
        times = sorted(metrics['response_times'])
        avg_time = mean(times)
        min_time = min(times)
        max_time = max(times)
        p50 = times[int(len(times) * 0.50)]
        p95 = times[int(len(times) * 0.95)]
        p99 = times[int(len(times) * 0.99)]
        
        print(f"\n⚡ THROUGHPUT:")
        rps = metrics['requests']/duration
        print(f"  Requests Per Second (RPS): {rps:.2f} req/sec")
        
        print(f"\n⏱️  RESPONSE TIME METRICS (ms):")
        print(f"  Average:    {avg_time:.2f} ms")
        print(f"  Minimum:    {min_time:.2f} ms")
        print(f"  Maximum:    {max_time:.2f} ms")
        print(f"  P50 (50%):  {p50:.2f} ms")
        print(f"  P95 (95%):  {p95:.2f} ms")
        print(f"  P99 (99%):  {p99:.2f} ms")
        
        print(f"\n📈 REQUESTS BY ENDPOINT:")
        for endpoint in sorted(metrics['endpoint_stats'].keys()):
            stats = metrics['endpoint_stats'][endpoint]
            if stats['count'] > 0:
                avg = mean(stats['times'])
                print(f"  {endpoint}")
                print(f"    Count: {stats['count']} requests")
                print(f"    Avg Response: {avg:.2f} ms")
                if stats['errors'] > 0:
                    error_pct = (stats['errors']/stats['count']*100)
                    print(f"    Errors: {stats['errors']} ({error_pct:.1f}%)")
        
        # Performance assessment & comparison
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if success_pct >= 95 and rps > 150 and avg_time < 700:
            rating = "✅ EXCELLENT"
        elif success_pct >= 80 and rps > 100 and avg_time < 800:
            rating = "✅ GOOD"
        elif success_pct >= 50 and rps > 50:
            rating = "⚠️  FAIR"
        else:
            rating = "❌ POOR"
        
        print(f"  {rating} - System with JWT authentication")
        print(f"     {rps:.0f} RPS, {avg_time:.0f}ms avg, {success_pct:.1f}% success rate")
        
        # Comparison to baseline (from initial load test)
        print(f"\n📊 COMPARISON TO BASELINE:")
        print(f"  Previous (no auth): 150 RPS, 639ms avg, 40.8% success")
        print(f"  Current (with auth): {rps:.0f} RPS, {avg_time:.0f}ms avg, {success_pct:.1f}% success")
        
        if success_pct > 40.8:
            print(f"  ✅ Success rate improved by {success_pct - 40.8:.1f}%")
        if rps > 150:
            print(f"  ✅ Throughput improved by {(rps/150 - 1)*100:.1f}%")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_time > 800:
            print(f"  • Add database indexes on email, user_id, crop_id columns")
            print(f"  • Implement query result caching (Redis)")
        if success_pct < 90:
            print(f"  • Implement database connection pooling (SQLAlchemy)")
            print(f"  • Check for database connection limits")
        if rps < 150:
            print(f"  • Profile slow queries with EXPLAIN")
            print(f"  • Add indexes to frequently queried columns")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("Setting up test users and authentication...")
    print(f"Registering and authenticating {CONCURRENT_USERS} users...\n")
    
    # Setup phase - register and authenticate all users
    setup_threads = []
    for i in range(CONCURRENT_USERS):
        t = threading.Thread(target=setup_user, args=(i,), daemon=True)
        t.start()
        setup_threads.append(t)
    
    # Wait for setup to complete
    for t in setup_threads:
        t.join(timeout=120)
    
    authenticated = len(user_tokens)
    print(f"Successfully authenticated {authenticated}/{CONCURRENT_USERS} users\n")
    
    if authenticated == 0:
        print("ERROR: Could not authenticate any users. Aborting test.")
        exit(1)
    
    print(f"Starting {TEST_DURATION_SECONDS} second load test...")
    print(f"Distribution: 20% market/prices, 20% market/mandis, 20% disease/reports,")
    print(f"              20% crop/recommend, 20% auth/profile\n")
    
    # Start load test
    metrics['start_time'] = time.time()
    
    threads = []
    for i in range(CONCURRENT_USERS):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
        threads.append(t)
    
    # Wait for test to complete
    for t in threads:
        t.join(timeout=TEST_DURATION_SECONDS + 10)
    
    # Print results
    print_results()
