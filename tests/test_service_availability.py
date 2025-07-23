#!/usr/bin/env python3
"""
Service Availability Test Script
Tests the availability of each microservice
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

import requests
import json
import time
from datetime import datetime
from test_helpers import ServiceHealthChecker, TestReporter, APITestHelper, TestDataGenerator

class ServiceAvailabilityTester:
    """Test availability of all microservices"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000', frontend_url='http://127.0.0.1:3002'):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.reporter = TestReporter()
        self.services = {
            'auth_service': f'{backend_url}/api/auth',
            'plan_service': f'{backend_url}/api/plans',
            'payment_service': f'{backend_url}/api/payments',
            'user_service': f'{backend_url}/api/users',
            'health_service': f'{backend_url}/api/health',
            'frontend_service': frontend_url
        }
    
    def test_service_ping(self, service_name, service_url):
        """Test if service responds to basic requests"""
        start_time = time.time()
        try:
            if service_name == 'frontend_service':
                # Test frontend availability
                response = requests.get(service_url, timeout=10)
                success = response.status_code in [200, 302]  # 302 for redirects
            elif service_name == 'health_service':
                # Test health endpoint
                response = requests.get(f'{service_url}/', timeout=10)
                success = response.status_code == 200
            else:
                # Test API endpoints (may return 401 for auth required)
                response = requests.options(service_url, timeout=10)
                success = response.status_code != 404  # Service exists
            
            duration = time.time() - start_time
            
            if success:
                self.reporter.add_test_result(
                    f'{service_name}_availability',
                    'passed',
                    duration,
                    {'response_code': response.status_code, 'response_time': duration}
                )
                return True, response.status_code, duration
            else:
                self.reporter.add_test_result(
                    f'{service_name}_availability',
                    'failed',
                    duration,
                    {'response_code': response.status_code, 'error': 'Service not available'}
                )
                return False, response.status_code, duration
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.reporter.add_test_result(
                f'{service_name}_availability',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None, duration
    
    def test_service_health(self):
        """Test detailed service health"""
        start_time = time.time()
        try:
            response = requests.get(f'{self.backend_url}/api/health/detailed', timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                overall_status = health_data.get('status', 'unknown')
                services_status = health_data.get('services', {})
                
                # Test overall health
                if overall_status == 'healthy':
                    self.reporter.add_test_result(
                        'overall_health',
                        'passed',
                        duration,
                        {'services_count': len(services_status)}
                    )
                else:
                    self.reporter.add_test_result(
                        'overall_health',
                        'failed',
                        duration,
                        {'status': overall_status}
                    )
                
                # Test individual service health
                for service_name, service_health in services_status.items():
                    service_status = service_health.get('status', 'unknown')
                    if service_status == 'healthy':
                        self.reporter.add_test_result(
                            f'{service_name}_health',
                            'passed',
                            0.1,  # Minimal time for individual service check
                            service_health
                        )
                    else:
                        self.reporter.add_test_result(
                            f'{service_name}_health',
                            'failed',
                            0.1,
                            service_health
                        )
                
                return True, health_data
            else:
                self.reporter.add_test_result(
                    'overall_health',
                    'failed',
                    duration,
                    {'response_code': response.status_code}
                )
                return False, None
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.reporter.add_test_result(
                'overall_health',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_service_endpoints(self):
        """Test specific service endpoints"""
        # Test authentication endpoints
        auth_endpoints = [
            ('POST', f'{self.backend_url}/api/auth/register'),
            ('POST', f'{self.backend_url}/api/auth/login'),
            ('POST', f'{self.backend_url}/api/auth/refresh'),
            ('POST', f'{self.backend_url}/api/auth/logout')
        ]
        
        for method, endpoint in auth_endpoints:
            start_time = time.time()
            try:
                if method == 'POST':
                    response = requests.post(endpoint, json={}, timeout=10)
                else:
                    response = requests.get(endpoint, timeout=10)
                
                duration = time.time() - start_time
                
                # For auth endpoints, we expect 400 (bad request) or 401 (unauthorized)
                # but not 404 (not found) or 500 (server error)
                success = response.status_code not in [404, 500, 502, 503]
                
                endpoint_name = endpoint.split('/')[-1]
                if success:
                    self.reporter.add_test_result(
                        f'auth_{endpoint_name}_endpoint',
                        'passed',
                        duration,
                        {'response_code': response.status_code}
                    )
                else:
                    self.reporter.add_test_result(
                        f'auth_{endpoint_name}_endpoint',
                        'failed',
                        duration,
                        {'response_code': response.status_code}
                    )
                    
            except requests.exceptions.RequestException as e:
                duration = time.time() - start_time
                self.reporter.add_test_result(
                    f'auth_{endpoint_name}_endpoint',
                    'failed',
                    duration,
                    {'error': str(e)}
                )
    
    def test_database_connectivity(self):
        """Test database connectivity through health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f'{self.backend_url}/api/health/stats', timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                stats_data = response.json()
                if stats_data.get('success', False):
                    self.reporter.add_test_result(
                        'database_connectivity',
                        'passed',
                        duration,
                        stats_data.get('stats', {})
                    )
                    return True, stats_data
                else:
                    self.reporter.add_test_result(
                        'database_connectivity',
                        'failed',
                        duration,
                        {'error': stats_data.get('error', 'Unknown error')}
                    )
                    return False, None
            else:
                self.reporter.add_test_result(
                    'database_connectivity',
                    'failed',
                    duration,
                    {'response_code': response.status_code}
                )
                return False, None
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.reporter.add_test_result(
                'database_connectivity',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def run_all_tests(self):
        """Run all availability tests"""
        print("🔍 Starting Service Availability Tests...")
        print("=" * 50)
        
        # Test individual service availability
        print("\n📡 Testing Service Availability...")
        for service_name, service_url in self.services.items():
            print(f"Testing {service_name}...", end=" ")
            success, status_code, duration = self.test_service_ping(service_name, service_url)
            if success:
                print(f"✅ Available (HTTP {status_code}) - {duration:.2f}s")
            else:
                print(f"❌ Unavailable (HTTP {status_code}) - {duration:.2f}s")
        
        # Test service health
        print("\n🏥 Testing Service Health...")
        health_success, health_data = self.test_service_health()
        if health_success:
            print("✅ Health check passed")
            if health_data and 'services' in health_data:
                for service_name, service_health in health_data['services'].items():
                    status = service_health.get('status', 'unknown')
                    print(f"  - {service_name}: {status}")
        else:
            print("❌ Health check failed")
        
        # Test database connectivity
        print("\n🗄️  Testing Database Connectivity...")
        db_success, db_stats = self.test_database_connectivity()
        if db_success:
            print("✅ Database connectivity verified")
            if db_stats and 'stats' in db_stats:
                stats = db_stats['stats']
                print(f"  - Users: {stats.get('users_count', 'N/A')}")
                print(f"  - Plans: {stats.get('plans_count', 'N/A')}")
                print(f"  - Transactions: {stats.get('transactions_count', 'N/A')}")
        else:
            print("❌ Database connectivity failed")
        
        # Test service endpoints
        print("\n🔗 Testing Service Endpoints...")
        self.test_service_endpoints()
        print("✅ Endpoint tests completed")
        
        # Generate summary
        print("\n📊 Test Summary")
        print("=" * 50)
        summary = self.reporter.generate_summary()
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        # Export results
        report_file = self.reporter.export_results('service_availability_report.json')
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return summary['success_rate'] == 100.0

def main():
    """Main function to run service availability tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test service availability')
    parser.add_argument('--backend-url', default='http://127.0.0.1:5000',
                       help='Backend service URL')
    parser.add_argument('--frontend-url', default='http://127.0.0.1:3002',
                       help='Frontend service URL')
    parser.add_argument('--wait-for-services', action='store_true',
                       help='Wait for services to be available before testing')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Timeout in seconds to wait for services')
    
    args = parser.parse_args()
    
    # Wait for services if requested
    if args.wait_for_services:
        print(f"⏳ Waiting for services to be available (timeout: {args.timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < args.timeout:
            try:
                response = requests.get(f'{args.backend_url}/api/health/', timeout=5)
                if response.status_code == 200:
                    print("✅ Backend service is available")
                    break
            except:
                pass
            time.sleep(2)
        else:
            print("❌ Timeout waiting for backend service")
            sys.exit(1)
    
    # Run tests
    tester = ServiceAvailabilityTester(args.backend_url, args.frontend_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All services are available and healthy!")
        sys.exit(0)
    else:
        print("\n⚠️  Some services have issues. Check the report for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
