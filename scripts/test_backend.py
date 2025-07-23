#!/usr/bin/env python3
"""
Backend API Testing Script
Tests all major API endpoints to ensure they're working correctly
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
API_BASE_URL = 'http://127.0.0.1:5000/api'
TEST_USER = {
    'username': 'john.doe',
    'password': 'password123'
}

class APITester:
    def __init__(self):
        self.access_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'response_time': response_time
        })
        print(f"{status} {test_name} ({response_time:.2f}ms) - {message}")
    
    def make_request(self, method, endpoint, data=None, auth_required=False):
        """Make HTTP request with error handling"""
        url = f"{API_BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
            
            response_time = (time.time() - start_time) * 1000
            
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            return None, 0
    
    def test_health_check(self):
        """Test basic health check"""
        response, response_time = self.make_request('GET', '/health/')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('status') == 'healthy'
            message = f"Status: {data.get('status')}"
        else:
            success = False
            message = "Health check failed"
        
        self.log_test("Health Check", success, message, response_time)
        return success
    
    def test_detailed_health_check(self):
        """Test detailed health check"""
        response, response_time = self.make_request('GET', '/health/detailed')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('status') == 'healthy'
            services = data.get('services', {})
            healthy_services = sum(1 for s in services.values() if s.get('status') == 'healthy')
            message = f"Services: {healthy_services}/{len(services)} healthy"
        else:
            success = False
            message = "Detailed health check failed"
        
        self.log_test("Detailed Health Check", success, message, response_time)
        return success
    
    def test_login(self):
        """Test user login"""
        response, response_time = self.make_request('POST', '/auth/login', TEST_USER)
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                self.access_token = data.get('access_token')
                message = f"Logged in as {data.get('user', {}).get('username')}"
            else:
                message = data.get('error', 'Login failed')
        else:
            success = False
            message = "Login request failed"
        
        self.log_test("User Login", success, message, response_time)
        return success
    
    def test_get_profile(self):
        """Test get user profile"""
        response, response_time = self.make_request('GET', '/auth/profile', auth_required=True)
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                user = data.get('user', {})
                message = f"Profile: {user.get('first_name')} {user.get('last_name')}"
            else:
                message = data.get('error', 'Failed to get profile')
        else:
            success = False
            message = "Profile request failed"
        
        self.log_test("Get Profile", success, message, response_time)
        return success
    
    def test_get_plans(self):
        """Test get all plans"""
        response, response_time = self.make_request('GET', '/plans/')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                plans = data.get('plans', [])
                message = f"Found {len(plans)} plans"
            else:
                message = data.get('error', 'Failed to get plans')
        else:
            success = False
            message = "Plans request failed"
        
        self.log_test("Get Plans", success, message, response_time)
        return success
    
    def test_get_categories(self):
        """Test get plan categories"""
        response, response_time = self.make_request('GET', '/plans/categories')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                categories = data.get('categories', [])
                message = f"Found {len(categories)} categories"
            else:
                message = data.get('error', 'Failed to get categories')
        else:
            success = False
            message = "Categories request failed"
        
        self.log_test("Get Categories", success, message, response_time)
        return success
    
    def test_get_current_plan(self):
        """Test get current user plan"""
        response, response_time = self.make_request('GET', '/plans/current-plan', auth_required=True)
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                current_plan = data.get('current_plan')
                if current_plan:
                    message = f"Current plan: {current_plan.get('plan', {}).get('name')}"
                else:
                    message = "No current plan"
            else:
                message = data.get('error', 'Failed to get current plan')
        else:
            success = False
            message = "Current plan request failed"
        
        self.log_test("Get Current Plan", success, message, response_time)
        return success
    
    def test_get_payment_methods(self):
        """Test get payment methods"""
        response, response_time = self.make_request('GET', '/payments/methods')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                methods = data.get('payment_methods', [])
                message = f"Found {len(methods)} payment methods"
            else:
                message = data.get('error', 'Failed to get payment methods')
        else:
            success = False
            message = "Payment methods request failed"
        
        self.log_test("Get Payment Methods", success, message, response_time)
        return success
    
    def test_get_dashboard(self):
        """Test get user dashboard"""
        response, response_time = self.make_request('GET', '/users/dashboard', auth_required=True)
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                dashboard = data.get('dashboard', {})
                stats = dashboard.get('statistics', {})
                message = f"Dashboard loaded - {stats.get('active_plans', 0)} active plans"
            else:
                message = data.get('error', 'Failed to get dashboard')
        else:
            success = False
            message = "Dashboard request failed"
        
        self.log_test("Get Dashboard", success, message, response_time)
        return success
    
    def test_service_testing(self):
        """Test service testing endpoint"""
        response, response_time = self.make_request('GET', '/health/test-services')
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get('overall_status') == 'healthy'
            services = data.get('services', {})
            healthy_services = sum(1 for s in services.values() if s.get('status') == 'healthy')
            message = f"Service tests: {healthy_services}/{len(services)} passed"
        else:
            success = False
            message = "Service testing failed"
        
        self.log_test("Service Testing", success, message, response_time)
        return success
    
    def test_error_injection(self):
        """Test error injection functionality"""
        # Inject error
        inject_data = {
            'service': 'auth',
            'error_type': 'timeout',
            'duration': 5
        }
        response, response_time = self.make_request('POST', '/health/inject-error', inject_data)
        
        if response and response.status_code == 200:
            data = response.json()
            inject_success = data.get('success', False)
            
            # Clear errors
            clear_response, _ = self.make_request('POST', '/health/clear-errors')
            clear_success = clear_response and clear_response.status_code == 200
            
            success = inject_success and clear_success
            message = "Error injection and clearing successful"
        else:
            success = False
            message = "Error injection failed"
        
        self.log_test("Error Injection", success, message, response_time)
        return success
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Backend API Tests")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_detailed_health_check,
            self.test_login,
            self.test_get_profile,
            self.test_get_plans,
            self.test_get_categories,
            self.test_get_current_plan,
            self.test_get_payment_methods,
            self.test_get_dashboard,
            self.test_service_testing,
            self.test_error_injection
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(0.1)  # Small delay between tests
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend is working correctly.")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Check the backend setup.")
            return False
    
    def print_summary(self):
        """Print detailed test summary"""
        print("\n📋 Detailed Test Summary:")
        print("-" * 60)
        
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"{result['test']:<25} | {status:<4} | {result['response_time']:>6.1f}ms | {result['message']}")

def main():
    """Main function"""
    print("Telecom Backend API Tester")
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tester = APITester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
