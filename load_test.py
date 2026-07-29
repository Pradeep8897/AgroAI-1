"""
AgroAI Backend Load Testing
Baseline/Load Test: 100 concurrent users for 1 minute
"""

from locust import HttpUser, task, between, events
import time
import json

# Test Configuration
API_BASE_URL = "http://localhost:5000"  # Change if backend running elsewhere
DURATION_SECONDS = 60  # 1 minute
CONCURRENT_USERS = 100

# Metrics collection
class TestMetrics:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.requests_per_endpoint = {}
    
    def record_request(self, endpoint, response_time, success):
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if endpoint not in self.requests_per_endpoint:
            self.requests_per_endpoint[endpoint] = {'count': 0, 'times': []}
        
        self.requests_per_endpoint[endpoint]['count'] += 1
        self.requests_per_endpoint[endpoint]['times'].append(response_time)
    
    def get_stats(self):
        if not self.response_times:
            return None
        
        times = sorted(self.response_times)
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 1
        
        return {
            'duration': total_time,
            'total_requests': self.total_requests,
            'successful': self.successful_requests,
            'failed': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            'rps': self.total_requests / total_time,
            'response_time_avg': sum(times) / len(times),
            'response_time_min': min(times),
            'response_time_max': max(times),
            'response_time_p50': times[int(len(times) * 0.5)],
            'response_time_p95': times[int(len(times) * 0.95)],
            'response_time_p99': times[int(len(times) * 0.99)],
        }

metrics = TestMetrics()

class AgroAIUser(HttpUser):
    """
    Load test user simulating real API usage
    """
    wait_time = between(0.1, 0.5)  # Wait 0.1-0.5 seconds between requests for more realistic testing
    
    def on_start(self):
        """Initialize test user"""
        if not metrics.start_time:
            metrics.start_time = time.time()
        
        # Try to login first
        try:
            self.login_token = None
            response = self.client.post(
                f"{API_BASE_URL}/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "password123"
                },
                catch_response=True
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.login_token = data.get('token')
                except:
                    pass
        except:
            pass
    
    @task(4)
    def get_public_endpoints(self):
        """Test public endpoints (4x weight)"""
        endpoints = [
            "/api/disease/reports",
            "/api/market/prices",
            "/api/market/mandis",
        ]
        for endpoint in endpoints:
            start = time.time()
            try:
                response = self.client.get(
                    f"{API_BASE_URL}{endpoint}",
                    timeout=5,
                    catch_response=True
                )
                elapsed = (time.time() - start) * 1000  # Convert to ms
                success = response.status_code == 200
                metrics.record_request(endpoint, elapsed, success)
                
                if success:
                    response.success()
                else:
                    response.failure(f"Status: {response.status_code}")
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                metrics.record_request(endpoint, elapsed, False)
    
    @task(3)
    def test_crop_endpoints(self):
        """Test crop recommendation endpoints (3x weight)"""
        start = time.time()
        try:
            response = self.client.post(
                f"{API_BASE_URL}/api/crop/recommend",
                json={
                    "N": 50,
                    "P": 30,
                    "K": 20,
                    "ph": 6.5,
                    "temperature": 25,
                    "humidity": 60,
                    "rainfall": 500
                },
                timeout=5,
                catch_response=True
            )
            elapsed = (time.time() - start) * 1000
            success = response.status_code in [200, 400]  # 400 is OK (no auth)
            metrics.record_request("/api/crop/recommend", elapsed, success)
            
            if success:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            metrics.record_request("/api/crop/recommend", elapsed, False)
    
    @task(2)
    def test_disease_endpoints(self):
        """Test disease endpoints (2x weight)"""
        start = time.time()
        try:
            response = self.client.get(
                f"{API_BASE_URL}/api/disease/reports",
                timeout=5,
                catch_response=True
            )
            elapsed = (time.time() - start) * 1000
            success = response.status_code in [200, 404]
            metrics.record_request("/api/disease/reports", elapsed, success)
            
            if success:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            metrics.record_request("/api/disease/details", elapsed, False)
    
    @task(1)
    def test_auth_endpoints(self):
        """Test authentication endpoints (1x weight)"""
        start = time.time()
        try:
            response = self.client.post(
                f"{API_BASE_URL}/api/auth/login",
                json={
                    "email": f"loadtest{int(time.time()*1000) % 1000}@example.com",
                    "password": "testpass123"
                },
                timeout=5,
                catch_response=True
            )
            elapsed = (time.time() - start) * 1000
            success = response.status_code in [200, 401]  # 401 is OK (invalid creds)
            metrics.record_request("/api/auth/login", elapsed, success)
            
            if success:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            metrics.record_request("/api/auth/login", elapsed, False)

# Event handlers
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final report when test completes"""
    metrics.end_time = time.time()
    print_report()

def print_report():
    """Print formatted load test report"""
    stats = metrics.get_stats()
    
    print("\n" + "="*80)
    print("AGROAI BACKEND - LOAD TEST REPORT")
    print("="*80)
    print(f"\nTest Configuration:")
    print(f"  Concurrent Users: {CONCURRENT_USERS}")
    print(f"  Duration: {DURATION_SECONDS} seconds")
    print(f"  API Endpoint: {API_BASE_URL}")
    
    if not stats:
        print("\n⚠️  No requests completed")
        return
    
    print(f"\n📊 OVERALL METRICS:")
    print(f"  Total Requests: {stats['total_requests']:,}")
    print(f"  Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"  Failed: {stats['failed']}")
    print(f"  Duration: {stats['duration']:.2f} seconds")
    
    print(f"\n⚡ THROUGHPUT:")
    print(f"  Requests Per Second (RPS): {stats['rps']:.2f} req/sec")
    print(f"  Average Requests/Min: {stats['rps'] * 60:.0f} req/min")
    
    print(f"\n⏱️  RESPONSE TIME METRICS:")
    print(f"  Average:    {stats['response_time_avg']:.2f} ms")
    print(f"  Minimum:    {stats['response_time_min']:.2f} ms")
    print(f"  Maximum:    {stats['response_time_max']:.2f} ms")
    print(f"  P50 (50%):  {stats['response_time_p50']:.2f} ms")
    print(f"  P95 (95%):  {stats['response_time_p95']:.2f} ms")
    print(f"  P99 (99%):  {stats['response_time_p99']:.2f} ms")
    
    print(f"\n📈 REQUESTS BY ENDPOINT:")
    for endpoint in sorted(metrics.requests_per_endpoint.keys()):
        data = metrics.requests_per_endpoint[endpoint]
        count = data['count']
        avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
        print(f"  {endpoint}")
        print(f"    Count: {count} requests")
        print(f"    Avg Response: {avg_time:.2f} ms")
    
    print(f"\n{'='*80}")
    
    # Performance assessment
    print(f"\n🎯 PERFORMANCE ASSESSMENT:")
    rps = stats['rps']
    avg_rt = stats['response_time_avg']
    
    if rps > 500 and avg_rt < 100:
        print(f"  ✅ EXCELLENT - System is performing very well")
        print(f"     {rps:.0f} RPS with {avg_rt:.0f}ms avg response")
    elif rps > 200 and avg_rt < 300:
        print(f"  ✅ GOOD - System performance is acceptable")
        print(f"     {rps:.0f} RPS with {avg_rt:.0f}ms avg response")
    elif rps > 50 and avg_rt < 1000:
        print(f"  ⚠️  FAIR - System can handle load but may need optimization")
        print(f"     {rps:.0f} RPS with {avg_rt:.0f}ms avg response")
    else:
        print(f"  ❌ POOR - System struggling under load")
        print(f"     {rps:.0f} RPS with {avg_rt:.0f}ms avg response")
        print(f"     Recommendations: Optimize queries, add caching, scale horizontally")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    print("Load testing configured. Use locust command to run:")
    print(f"  locust -f load_test.py --host={API_BASE_URL} -u {CONCURRENT_USERS} -r {CONCURRENT_USERS} --run-time 1m --headless")
