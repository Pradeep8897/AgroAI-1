"""
Simple Direct Load Test - Measures real response times without Locust framework overhead
100 concurrent users, 1 minute duration
"""

import requests
import threading
import time
import json
from collections import defaultdict
from statistics import mean, stdev

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
    'end_time': None
}

# Test endpoints (actual routes from backend)
ENDPOINTS = [
    ('GET', '/api/market/prices'),
    ('GET', '/api/market/mandis'),
    ('GET', '/api/disease/reports'),
    ('POST', '/api/crop/recommend', {'N': 50, 'P': 30, 'K': 20, 'ph': 6.5, 'temperature': 25, 'humidity': 60, 'rainfall': 500}),
    ('POST', '/api/auth/login', {'email': 'test@example.com', 'password': 'password'}),
]

def make_request(method, endpoint, data=None):
    """Make a single API request and return response time"""
    try:
        start = time.time()
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        elapsed_ms = (time.time() - start) * 1000
        
        with metrics['lock']:
            metrics['requests'] += 1
            metrics['response_times'].append(elapsed_ms)
            metrics['endpoint_stats'][endpoint]['count'] += 1
            metrics['endpoint_stats'][endpoint]['times'].append(elapsed_ms)
            
            if response.status_code < 300:
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

def worker():
    """Worker thread - makes requests until test duration ends"""
    while time.time() - metrics['start_time'] < TEST_DURATION_SECONDS:
        # Randomly select endpoint with realistic distribution
        if len(ENDPOINTS[0]) == 2:  # GET endpoint
            method, endpoint = ENDPOINTS[0]
            data = None
        else:
            method, endpoint, data = ENDPOINTS[0]
        
        # Vary endpoints
        endpoint_choice = int((time.time() * 1000) % len(ENDPOINTS))
        endpoint_config = ENDPOINTS[endpoint_choice]
        
        if len(endpoint_config) == 2:
            method, endpoint = endpoint_config
            data = None
        else:
            method, endpoint, data = endpoint_config
        
        make_request(method, endpoint, data)
        # Minimal delay between requests
        time.sleep(0.01)

def print_results():
    """Print formatted results"""
    metrics['end_time'] = time.time()
    duration = metrics['end_time'] - metrics['start_time']
    
    print("\n" + "="*80)
    print("AGROAI BACKEND - SIMPLE LOAD TEST REPORT")
    print("="*80)
    
    print(f"\nTest Configuration:")
    print(f"  Concurrent Users: {CONCURRENT_USERS}")
    print(f"  Duration: {TEST_DURATION_SECONDS} seconds")
    print(f"  API Endpoint: {BASE_URL}")
    
    print(f"\n📊 OVERALL METRICS:")
    print(f"  Total Requests: {metrics['requests']}")
    print(f"  Successful: {metrics['successful']} ({metrics['successful']/metrics['requests']*100:.1f}%)")
    print(f"  Failed: {metrics['failed']}")
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
        print(f"  Requests Per Second (RPS): {metrics['requests']/duration:.2f} req/sec")
        
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
        rps = metrics['requests'] / duration
        if avg_time < 100 and rps > 500:
            print(f"  ✅ EXCELLENT - System performing well")
        elif avg_time < 300 and rps > 200:
            print(f"  ✅ GOOD - System performing adequately")
        elif avg_time < 1000 and rps > 50:
            print(f"  ⚠️  FAIR - System needs optimization")
        else:
            print(f"  ❌ POOR - System struggling under load")
        print(f"     {rps:.0f} RPS with {avg_time:.0f}ms avg response")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("Starting load test with 100 concurrent users...")
    print("Test will run for 60 seconds\n")
    
    # Start worker threads
    threads = []
    for i in range(CONCURRENT_USERS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
        # Stagger thread start
        time.sleep(0.01)
    
    # Wait for test to complete
    for t in threads:
        t.join(timeout=TEST_DURATION_SECONDS + 10)
    
    # Print results
    print_results()
