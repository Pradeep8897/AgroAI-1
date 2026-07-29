"""
Load Test with JWT Authentication
Tests realistic user scenarios with proper token handling
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
    'start_time': time.time(),
    'end_time': None,
    'auth_failures': 0
}

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
        
        return elapsed_ms, response.status_code, response
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        with metrics['lock']:
            metrics['requests'] += 1
            metrics['failed'] += 1
            metrics['response_times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['count'] += 1
            metrics['endpoint_stats'][endpoint]['times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['errors'] += 1
        return elapsed_ms, 'ERROR', None

def worker(user_id):
    """Worker thread - simulates a user with authentication"""
    # Each thread creates its own user/token
    user_email = f"loadtest_user_{user_id}@agroai.com"
    user_password = f"TestPass{user_id}123"
    user_token = None
    token_time = 0
    
    # Register user once
    register_data = {
        "username": f"User{user_id}",
        "email": user_email,
        "password": user_password,
        "role": "farmer"
    }
    make_request('POST', '/api/auth/register', register_data)
    
    while time.time() - metrics['start_time'] < TEST_DURATION_SECONDS:
        # Refresh token if expired (every 10 minutes or first time)
        if not user_token or (time.time() - token_time) > 600:
            login_data = {
                "email": user_email,
                "password": user_password
            }
            elapsed, status, response = make_request('POST', '/api/auth/login', login_data)
            
            if status == 201 and response:
                try:
                    result = response.json()
                    if result.get('token'):
                        user_token = result['token']
                        token_time = time.time()
                    else:
                        with metrics['lock']:
                            metrics['auth_failures'] += 1
                except:
                    pass
        
        # Make authenticated requests
        if user_token:
            headers = {'Authorization': f'Bearer {user_token}'}
            
            # Simulate realistic user workflow
            scenario = int((time.time() * 1000) % 4)
            
            if scenario == 0:
                # Get market prices (unprotected)
                make_request('GET', '/api/market/prices', headers=headers)
            
            elif scenario == 1:
                # Get market mandis (unprotected)
                make_request('GET', '/api/market/mandis', headers=headers)
            
            elif scenario == 2:
                # Get disease reports (protected)
                make_request('GET', '/api/disease/reports', headers=headers)
            
            elif scenario == 3:
                # Get crop recommendation (protected)
                crop_data = {
                    'N': 50, 'P': 30, 'K': 20, 'ph': 6.5,
                    'temperature': 25, 'humidity': 60, 'rainfall': 500
                }
                make_request('POST', '/api/crop/recommend', crop_data, headers)
        
        # Small delay between requests
        time.sleep(0.05)

def print_results():
    """Print formatted results"""
    metrics['end_time'] = time.time()
    duration = metrics['end_time'] - metrics['start_time']
    
    print("\n" + "="*80)
    print("AGROAI BACKEND - LOAD TEST WITH JWT AUTHENTICATION")
    print("="*80)
    
    print(f"\nTest Configuration:")
    print(f"  Concurrent Users: {CONCURRENT_USERS}")
    print(f"  Duration: {TEST_DURATION_SECONDS} seconds")
    print(f"  API Endpoint: {BASE_URL}")
    print(f"  Auth Method: JWT Bearer Token")
    
    print(f"\n📊 OVERALL METRICS:")
    print(f"  Total Requests: {metrics['requests']}")
    print(f"  Successful: {metrics['successful']} ({metrics['successful']/max(1, metrics['requests'])*100:.1f}%)")
    print(f"  Failed: {metrics['failed']}")
    print(f"  Auth Failures: {metrics['auth_failures']}")
    print(f"  Actual Duration: {duration:.2f} seconds")
    
    if metrics['response_times']:
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
                    print(f"    Errors: {stats['errors']}")
        
        # Performance assessment
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        success_rate = metrics['successful']/max(1, metrics['requests'])*100
        
        if success_rate >= 95 and rps > 150 and avg_time < 700:
            print(f"  ✅ EXCELLENT - System performing well with proper auth")
        elif success_rate >= 80 and rps > 100 and avg_time < 800:
            print(f"  ✅ GOOD - System performing adequately")
        elif success_rate >= 50 and rps > 50:
            print(f"  ⚠️  FAIR - System needs optimization")
        else:
            print(f"  ❌ POOR - System struggling under load")
        
        print(f"     {rps:.0f} RPS with {avg_time:.0f}ms avg response ({success_rate:.1f}% success)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_time > 800:
            print(f"  • Response times are high - consider adding database indexes")
            print(f"  • Implement caching for frequently accessed endpoints")
        if success_rate < 90:
            print(f"  • High failure rate suggests database connection issues")
            print(f"  • Consider implementing connection pooling")
        if rps < 150:
            print(f"  • Throughput is lower than expected")
            print(f"  • Profile the database queries for N+1 problems")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("Starting load test with JWT authentication...")
    print(f"Test will run for {TEST_DURATION_SECONDS} seconds with {CONCURRENT_USERS} concurrent users\n")
    
    # Start worker threads
    threads = []
    for i in range(CONCURRENT_USERS):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        # Stagger thread start
        time.sleep(0.01)
    
    # Wait for test to complete
    for t in threads:
        t.join(timeout=TEST_DURATION_SECONDS + 30)
    
    # Print results
    print_results()
