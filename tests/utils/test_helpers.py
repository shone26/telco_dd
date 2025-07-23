"""
Test utility functions and helpers
"""
import json
import time
import random
import string
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class TestDataGenerator:
    """Generate test data for various test scenarios"""
    
    @staticmethod
    def generate_user_data(username_suffix: str = None) -> Dict[str, Any]:
        """Generate test user data"""
        suffix = username_suffix or ''.join(random.choices(string.ascii_lowercase, k=5))
        return {
            'username': f'testuser_{suffix}',
            'email': f'test_{suffix}@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': f'+91-{random.randint(7000000000, 9999999999)}'
        }
    
    @staticmethod
    def generate_plan_data(name_suffix: str = None) -> Dict[str, Any]:
        """Generate test plan data"""
        suffix = name_suffix or ''.join(random.choices(string.ascii_lowercase, k=5))
        return {
            'name': f'Test Plan {suffix}',
            'description': f'Test plan for {suffix}',
            'price': random.uniform(100, 1000),
            'data_limit': f'{random.randint(1, 10)}GB',
            'call_minutes': random.randint(100, 1000),
            'sms_limit': random.randint(100, 1000),
            'validity_days': random.choice([30, 60, 90]),
            'is_available': True,
            'is_popular': random.choice([True, False])
        }
    
    @staticmethod
    def generate_payment_data(plan_id: int, payment_method: str = 'credit_card') -> Dict[str, Any]:
        """Generate test payment data"""
        base_data = {
            'plan_id': plan_id,
            'payment_method': payment_method
        }
        
        if payment_method == 'credit_card':
            base_data.update({
                'card_number': '4111111111111111',
                'expiry_month': random.randint(1, 12),
                'expiry_year': random.randint(2025, 2030),
                'cvv': f'{random.randint(100, 999)}',
                'cardholder_name': 'Test User'
            })
        elif payment_method == 'debit_card':
            base_data.update({
                'card_number': '4111111111111111',
                'expiry_month': random.randint(1, 12),
                'expiry_year': random.randint(2025, 2030),
                'cvv': f'{random.randint(100, 999)}',
                'cardholder_name': 'Test User'
            })
        elif payment_method == 'upi':
            base_data.update({
                'upi_id': f'testuser@{random.choice(["paytm", "gpay", "phonepe"])}'
            })
        elif payment_method == 'net_banking':
            base_data.update({
                'bank_code': random.choice(['HDFC', 'ICICI', 'SBI', 'AXIS'])
            })
        
        return base_data
    
    @staticmethod
    def generate_invalid_card_data() -> Dict[str, Any]:
        """Generate invalid card data for testing"""
        return {
            'card_number': '1234567890123456',  # Invalid card number
            'expiry_month': 13,  # Invalid month
            'expiry_year': 2020,  # Expired year
            'cvv': '12345'  # Invalid CVV length
        }

class APITestHelper:
    """Helper class for API testing"""
    
    def __init__(self, client, base_url: str = '/api'):
        self.client = client
        self.base_url = base_url
    
    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a user and return response data"""
        response = self.client.post(
            f'{self.base_url}/auth/register',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        return json.loads(response.data), response.status_code
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login a user and return auth headers"""
        login_data = {'username': username, 'password': password}
        response = self.client.post(
            f'{self.base_url}/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            return {
                'headers': {'Authorization': f'Bearer {data["access_token"]}'},
                'user_data': data,
                'status_code': response.status_code
            }
        else:
            return {
                'headers': None,
                'user_data': json.loads(response.data),
                'status_code': response.status_code
            }
    
    def create_authenticated_user(self, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create and authenticate a user, return auth headers"""
        if user_data is None:
            user_data = TestDataGenerator.generate_user_data()
        
        # Register user
        register_result, register_status = self.register_user(user_data)
        if register_status != 201:
            raise Exception(f"Failed to register user: {register_result}")
        
        # Login user
        login_result = self.login_user(user_data['username'], user_data['password'])
        if login_result['status_code'] != 200:
            raise Exception(f"Failed to login user: {login_result}")
        
        return {
            'auth_headers': login_result['headers'],
            'user_data': user_data,
            'login_response': login_result['user_data']
        }
    
    def get_plans(self, auth_headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get available plans"""
        response = self.client.get(f'{self.base_url}/plans', headers=auth_headers)
        if response.status_code == 200:
            data = json.loads(response.data)
            return data.get('plans', [])
        return []
    
    def process_payment(self, payment_data: Dict[str, Any], auth_headers: Dict[str, str]) -> Dict[str, Any]:
        """Process a payment"""
        response = self.client.post(
            f'{self.base_url}/payments/process',
            data=json.dumps(payment_data),
            content_type='application/json',
            headers=auth_headers
        )
        return json.loads(response.data), response.status_code

class ServiceHealthChecker:
    """Check health of various services"""
    
    def __init__(self, client):
        self.client = client
    
    def check_service_health(self, service_name: str = None) -> Dict[str, Any]:
        """Check health of specific service or all services"""
        if service_name:
            # Check specific service health
            response = self.client.get(f'/api/health/detailed')
            if response.status_code == 200:
                data = json.loads(response.data)
                services = data.get('services', {})
                return {
                    'service': service_name,
                    'status': services.get(service_name, {}).get('status', 'unknown'),
                    'details': services.get(service_name, {})
                }
        else:
            # Check all services health
            response = self.client.get('/api/health/detailed')
            if response.status_code == 200:
                return json.loads(response.data)
        
        return {'status': 'error', 'message': 'Health check failed'}
    
    def wait_for_service_health(self, service_name: str, timeout: int = 30) -> bool:
        """Wait for a service to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            health = self.check_service_health(service_name)
            if health.get('status') == 'healthy':
                return True
            time.sleep(1)
        return False
    
    def check_all_services_healthy(self) -> bool:
        """Check if all services are healthy"""
        health = self.check_service_health()
        if health.get('status') == 'healthy':
            services = health.get('services', {})
            return all(service.get('status') == 'healthy' for service in services.values())
        return False

class ErrorInjector:
    """Inject errors into services for testing"""
    
    def __init__(self, client):
        self.client = client
    
    def inject_service_error(self, service: str, error_type: str, duration: int = 60) -> Dict[str, Any]:
        """Inject error into a specific service"""
        error_data = {
            'service': service,
            'error_type': error_type,
            'duration': duration
        }
        
        response = self.client.post(
            '/api/health/inject-error',
            data=json.dumps(error_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            return json.loads(response.data)
        else:
            return {'success': False, 'error': 'Failed to inject error'}
    
    def clear_all_errors(self) -> Dict[str, Any]:
        """Clear all injected errors"""
        response = self.client.post('/api/health/clear-errors')
        
        if response.status_code == 200:
            return json.loads(response.data)
        else:
            return {'success': False, 'error': 'Failed to clear errors'}
    
    def simulate_service_timeout(self, service: str, duration: int = 60) -> Dict[str, Any]:
        """Simulate service timeout"""
        return self.inject_service_error(service, 'timeout', duration)
    
    def simulate_service_failure(self, service: str, duration: int = 60) -> Dict[str, Any]:
        """Simulate service failure"""
        return self.inject_service_error(service, 'failure', duration)
    
    def simulate_service_unavailable(self, service: str, duration: int = 60) -> Dict[str, Any]:
        """Simulate service unavailable"""
        return self.inject_service_error(service, 'unavailable', duration)

class PerformanceTester:
    """Performance testing utilities"""
    
    def __init__(self, client):
        self.client = client
    
    def measure_response_time(self, endpoint: str, method: str = 'GET', 
                            headers: Dict[str, str] = None, 
                            data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Measure response time for an endpoint"""
        start_time = time.time()
        
        if method.upper() == 'GET':
            response = self.client.get(endpoint, headers=headers)
        elif method.upper() == 'POST':
            response = self.client.post(
                endpoint,
                data=json.dumps(data) if data else None,
                content_type='application/json',
                headers=headers
            )
        elif method.upper() == 'PUT':
            response = self.client.put(
                endpoint,
                data=json.dumps(data) if data else None,
                content_type='application/json',
                headers=headers
            )
        elif method.upper() == 'DELETE':
            response = self.client.delete(endpoint, headers=headers)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            'endpoint': endpoint,
            'method': method,
            'response_time_ms': response_time,
            'status_code': response.status_code,
            'success': 200 <= response.status_code < 300
        }
    
    def load_test_endpoint(self, endpoint: str, concurrent_requests: int = 10,
                          total_requests: int = 100, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Perform load testing on an endpoint"""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def make_request():
            try:
                result = self.measure_response_time(endpoint, headers=headers)
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(total_requests)]
            for future in futures:
                future.result()  # Wait for completion
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if results:
            response_times = [r['response_time_ms'] for r in results]
            successful_requests = [r for r in results if r['success']]
            
            return {
                'endpoint': endpoint,
                'total_requests': total_requests,
                'successful_requests': len(successful_requests),
                'failed_requests': len(results) - len(successful_requests),
                'errors': errors,
                'total_time_seconds': total_time,
                'requests_per_second': total_requests / total_time,
                'avg_response_time_ms': sum(response_times) / len(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'success_rate_percent': (len(successful_requests) / total_requests) * 100
            }
        else:
            return {
                'endpoint': endpoint,
                'total_requests': total_requests,
                'successful_requests': 0,
                'failed_requests': total_requests,
                'errors': errors,
                'total_time_seconds': total_time,
                'success_rate_percent': 0
            }

class DatabaseTestHelper:
    """Database testing utilities"""
    
    def __init__(self, app):
        self.app = app
    
    def reset_database(self):
        """Reset database to clean state"""
        with self.app.app_context():
            from app import db
            db.drop_all()
            db.create_all()
    
    def get_table_count(self, table_name: str) -> int:
        """Get count of records in a table"""
        with self.app.app_context():
            from app import db
            result = db.session.execute(db.text(f'SELECT COUNT(*) FROM {table_name}'))
            return result.scalar()
    
    def execute_query(self, query: str) -> Any:
        """Execute a raw SQL query"""
        with self.app.app_context():
            from app import db
            return db.session.execute(db.text(query))

class TestReporter:
    """Generate test reports"""
    
    def __init__(self):
        self.test_results = []
    
    def add_test_result(self, test_name: str, status: str, duration: float, 
                       details: Dict[str, Any] = None):
        """Add a test result"""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        })
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'passed'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'failed'])
        
        total_duration = sum(r['duration'] for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'average_duration': avg_duration,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_results(self, filename: str = None):
        """Export test results to JSON file"""
        if filename is None:
            filename = f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report_data = {
            'summary': self.generate_summary(),
            'test_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return filename

# Utility functions
def wait_for_condition(condition_func, timeout: int = 30, interval: float = 1.0) -> bool:
    """Wait for a condition to become true"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False

def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """Retry a function on failure"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)

def generate_test_data_file(filename: str, data_type: str, count: int = 10):
    """Generate test data file"""
    data = []
    
    if data_type == 'users':
        for i in range(count):
            data.append(TestDataGenerator.generate_user_data(f'user{i}'))
    elif data_type == 'plans':
        for i in range(count):
            data.append(TestDataGenerator.generate_plan_data(f'plan{i}'))
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

def cleanup_test_files(file_patterns: List[str]):
    """Clean up test files"""
    import glob
    import os
    
    for pattern in file_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except OSError:
                pass  # File might not exist or be in use
