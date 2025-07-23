#!/usr/bin/env python3
"""
Error Injection and Unhappy Path Test Script
Tests system behavior when services fail or errors are introduced
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

import requests
import json
import time
from datetime import datetime
from test_helpers import ErrorInjector, TestReporter, APITestHelper, TestDataGenerator

class ErrorInjectionTester:
    """Test system behavior with error injection"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000', frontend_url='http://127.0.0.1:3002'):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.reporter = TestReporter()
        self.session = requests.Session()
        self.services = ['auth', 'plan', 'payment', 'user']
        self.error_types = ['timeout', 'failure', 'unavailable']
        
    def setup_test_user(self):
        """Setup a test user for error testing"""
        user_data = TestDataGenerator.generate_user_data('error_test')
        
        # Register user
        response = self.session.post(
            f'{self.backend_url}/api/auth/register',
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            # Login user
            login_response = self.session.post(
                f'{self.backend_url}/api/auth/login',
                json={'username': user_data['username'], 'password': user_data['password']},
                timeout=10
            )
            
            if login_response.status_code == 200:
                result = login_response.json()
                self.auth_headers = {'Authorization': f'Bearer {result["access_token"]}'}
                return True, user_data
        
        return False, None
    
    def inject_service_error(self, service, error_type, duration=30):
        """Inject error into a specific service"""
        print(f"💉 Injecting {error_type} error into {service} service for {duration}s...")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f'{self.backend_url}/api/health/inject-error',
                json={
                    'service': service,
                    'error_type': error_type,
                    'duration': duration
                },
                timeout=10
            )
            
            test_duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ Error injected successfully")
                    self.reporter.add_test_result(
                        f'inject_{service}_{error_type}',
                        'passed',
                        test_duration,
                        {'service': service, 'error_type': error_type, 'duration': duration}
                    )
                    return True
                else:
                    print(f"  ❌ Error injection failed: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        f'inject_{service}_{error_type}',
                        'failed',
                        test_duration,
                        {'error': result.get('error')}
                    )
                    return False
            else:
                print(f"  ❌ Error injection request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    f'inject_{service}_{error_type}',
                    'failed',
                    test_duration,
                    {'status_code': response.status_code}
                )
                return False
                
        except Exception as e:
            test_duration = time.time() - start_time
            print(f"  ❌ Error injection error: {str(e)}")
            self.reporter.add_test_result(
                f'inject_{service}_{error_type}',
                'failed',
                test_duration,
                {'error': str(e)}
            )
            return False
    
    def clear_all_errors(self):
        """Clear all injected errors"""
        print("🧹 Clearing all injected errors...")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f'{self.backend_url}/api/health/clear-errors',
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("  ✅ All errors cleared")
                    self.reporter.add_test_result(
                        'clear_errors',
                        'passed',
                        duration
                    )
                    return True
                else:
                    print(f"  ❌ Failed to clear errors: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'clear_errors',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False
            else:
                print(f"  ❌ Clear errors request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'clear_errors',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Clear errors error: {str(e)}")
            self.reporter.add_test_result(
                'clear_errors',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False
    
    def test_auth_service_failure(self):
        """Test authentication service failure scenarios"""
        print("\n🔐 Testing Auth Service Failure Scenarios...")
        
        # Test login with auth service down
        self.inject_service_error('auth', 'failure', 30)
        time.sleep(2)  # Wait for error to take effect
        
        start_time = time.time()
        try:
            response = self.session.post(
                f'{self.backend_url}/api/auth/login',
                json={'username': 'testuser', 'password': 'testpass'},
                timeout=10
            )
            
            duration = time.time() - start_time
            
            # Should fail gracefully
            if response.status_code >= 500:
                print("  ✅ Auth service failure handled correctly (5xx error)")
                self.reporter.add_test_result(
                    'auth_failure_handling',
                    'passed',
                    duration,
                    {'status_code': response.status_code}
                )
            else:
                print(f"  ⚠️  Unexpected response: HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'auth_failure_handling',
                    'failed',
                    duration,
                    {'status_code': response.status_code, 'expected': '5xx'}
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ✅ Auth service failure caused exception (expected): {str(e)}")
            self.reporter.add_test_result(
                'auth_failure_handling',
                'passed',
                duration,
                {'error': str(e)}
            )
        
        self.clear_all_errors()
    
    def test_plan_service_timeout(self):
        """Test plan service timeout scenarios"""
        print("\n📋 Testing Plan Service Timeout Scenarios...")
        
        # Test plan browsing with timeout
        self.inject_service_error('plan', 'timeout', 30)
        time.sleep(2)
        
        start_time = time.time()
        try:
            response = self.session.get(
                f'{self.backend_url}/api/plans',
                headers=self.auth_headers,
                timeout=5  # Short timeout to trigger timeout handling
            )
            
            duration = time.time() - start_time
            
            if response.status_code >= 500 or duration >= 4:
                print("  ✅ Plan service timeout handled correctly")
                self.reporter.add_test_result(
                    'plan_timeout_handling',
                    'passed',
                    duration,
                    {'status_code': response.status_code, 'duration': duration}
                )
            else:
                print(f"  ⚠️  Unexpected response: HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'plan_timeout_handling',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            print("  ✅ Plan service timeout occurred (expected)")
            self.reporter.add_test_result(
                'plan_timeout_handling',
                'passed',
                duration,
                {'error': 'timeout'}
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ✅ Plan service timeout caused exception: {str(e)}")
            self.reporter.add_test_result(
                'plan_timeout_handling',
                'passed',
                duration,
                {'error': str(e)}
            )
        
        self.clear_all_errors()
    
    def test_payment_service_unavailable(self):
        """Test payment service unavailable scenarios"""
        print("\n💳 Testing Payment Service Unavailable Scenarios...")
        
        # Get a plan first
        plans_response = self.session.get(
            f'{self.backend_url}/api/plans',
            headers=self.auth_headers,
            timeout=10
        )
        
        if plans_response.status_code == 200:
            plans = plans_response.json().get('plans', [])
            if plans:
                plan_id = plans[0]['id']
                
                # Inject payment service error
                self.inject_service_error('payment', 'unavailable', 30)
                time.sleep(2)
                
                # Try to process payment
                payment_data = TestDataGenerator.generate_payment_data(plan_id)
                
                start_time = time.time()
                try:
                    response = self.session.post(
                        f'{self.backend_url}/api/payments/process',
                        json=payment_data,
                        headers=self.auth_headers,
                        timeout=10
                    )
                    
                    duration = time.time() - start_time
                    
                    if response.status_code >= 500:
                        print("  ✅ Payment service unavailable handled correctly")
                        self.reporter.add_test_result(
                            'payment_unavailable_handling',
                            'passed',
                            duration,
                            {'status_code': response.status_code}
                        )
                    else:
                        print(f"  ⚠️  Unexpected response: HTTP {response.status_code}")
                        self.reporter.add_test_result(
                            'payment_unavailable_handling',
                            'failed',
                            duration,
                            {'status_code': response.status_code}
                        )
                        
                except Exception as e:
                    duration = time.time() - start_time
                    print(f"  ✅ Payment service unavailable caused exception: {str(e)}")
                    self.reporter.add_test_result(
                        'payment_unavailable_handling',
                        'passed',
                        duration,
                        {'error': str(e)}
                    )
        
        self.clear_all_errors()
    
    def test_user_service_failure(self):
        """Test user service failure scenarios"""
        print("\n👤 Testing User Service Failure Scenarios...")
        
        # Test dashboard access with user service down
        self.inject_service_error('user', 'failure', 30)
        time.sleep(2)
        
        start_time = time.time()
        try:
            response = self.session.get(
                f'{self.backend_url}/api/users/dashboard',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code >= 500:
                print("  ✅ User service failure handled correctly")
                self.reporter.add_test_result(
                    'user_failure_handling',
                    'passed',
                    duration,
                    {'status_code': response.status_code}
                )
            else:
                print(f"  ⚠️  Unexpected response: HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'user_failure_handling',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ✅ User service failure caused exception: {str(e)}")
            self.reporter.add_test_result(
                'user_failure_handling',
                'passed',
                duration,
                {'error': str(e)}
            )
        
        self.clear_all_errors()
    
    def test_unhappy_path_scenarios(self):
        """Test various unhappy path scenarios"""
        print("\n😞 Testing Unhappy Path Scenarios...")
        
        # Test invalid login credentials
        print("  Testing invalid login credentials...")
        start_time = time.time()
        response = self.session.post(
            f'{self.backend_url}/api/auth/login',
            json={'username': 'nonexistent', 'password': 'wrongpass'},
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 401:
            print("    ✅ Invalid credentials rejected correctly")
            self.reporter.add_test_result(
                'invalid_login_handling',
                'passed',
                duration,
                {'status_code': response.status_code}
            )
        else:
            print(f"    ❌ Unexpected response: HTTP {response.status_code}")
            self.reporter.add_test_result(
                'invalid_login_handling',
                'failed',
                duration,
                {'status_code': response.status_code}
            )
        
        # Test invalid payment data
        print("  Testing invalid payment data...")
        invalid_payment = {
            'plan_id': 99999,  # Non-existent plan
            'payment_method': 'invalid_method',
            'card_number': '123',  # Invalid card
        }
        
        start_time = time.time()
        response = self.session.post(
            f'{self.backend_url}/api/payments/process',
            json=invalid_payment,
            headers=self.auth_headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code in [400, 404]:
            print("    ✅ Invalid payment data rejected correctly")
            self.reporter.add_test_result(
                'invalid_payment_handling',
                'passed',
                duration,
                {'status_code': response.status_code}
            )
        else:
            print(f"    ❌ Unexpected response: HTTP {response.status_code}")
            self.reporter.add_test_result(
                'invalid_payment_handling',
                'failed',
                duration,
                {'status_code': response.status_code}
            )
        
        # Test accessing non-existent plan
        print("  Testing non-existent plan access...")
        start_time = time.time()
        response = self.session.get(
            f'{self.backend_url}/api/plans/99999',
            headers=self.auth_headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 404:
            print("    ✅ Non-existent plan handled correctly")
            self.reporter.add_test_result(
                'nonexistent_plan_handling',
                'passed',
                duration,
                {'status_code': response.status_code}
            )
        else:
            print(f"    ❌ Unexpected response: HTTP {response.status_code}")
            self.reporter.add_test_result(
                'nonexistent_plan_handling',
                'failed',
                duration,
                {'status_code': response.status_code}
            )
        
        # Test unauthorized access
        print("  Testing unauthorized access...")
        start_time = time.time()
        response = self.session.get(
            f'{self.backend_url}/api/users/profile',
            timeout=10  # No auth headers
        )
        duration = time.time() - start_time
        
        if response.status_code == 401:
            print("    ✅ Unauthorized access blocked correctly")
            self.reporter.add_test_result(
                'unauthorized_access_handling',
                'passed',
                duration,
                {'status_code': response.status_code}
            )
        else:
            print(f"    ❌ Unexpected response: HTTP {response.status_code}")
            self.reporter.add_test_result(
                'unauthorized_access_handling',
                'failed',
                duration,
                {'status_code': response.status_code}
            )
    
    def test_cascade_failures(self):
        """Test cascade failure scenarios"""
        print("\n🌊 Testing Cascade Failure Scenarios...")
        
        # Inject multiple service failures
        print("  Injecting multiple service failures...")
        self.inject_service_error('auth', 'failure', 60)
        time.sleep(1)
        self.inject_service_error('payment', 'timeout', 60)
        time.sleep(1)
        self.inject_service_error('user', 'unavailable', 60)
        time.sleep(2)
        
        # Test system health under multiple failures
        start_time = time.time()
        try:
            response = self.session.get(
                f'{self.backend_url}/api/health/detailed',
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                overall_status = result.get('status', 'unknown')
                
                if overall_status == 'unhealthy':
                    print("    ✅ System correctly reports unhealthy status")
                    self.reporter.add_test_result(
                        'cascade_failure_detection',
                        'passed',
                        duration,
                        {'overall_status': overall_status}
                    )
                else:
                    print(f"    ⚠️  System reports status: {overall_status}")
                    self.reporter.add_test_result(
                        'cascade_failure_detection',
                        'failed',
                        duration,
                        {'overall_status': overall_status}
                    )
            else:
                print(f"    ❌ Health check failed: HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'cascade_failure_detection',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"    ✅ Health check failed as expected: {str(e)}")
            self.reporter.add_test_result(
                'cascade_failure_detection',
                'passed',
                duration,
                {'error': str(e)}
            )
        
        self.clear_all_errors()
    
    def test_recovery_scenarios(self):
        """Test service recovery scenarios"""
        print("\n🔄 Testing Service Recovery Scenarios...")
        
        # Inject temporary failure
        print("  Injecting temporary service failure...")
        self.inject_service_error('plan', 'failure', 10)  # Short duration
        time.sleep(2)
        
        # Verify service is down
        start_time = time.time()
        response = self.session.get(
            f'{self.backend_url}/api/plans',
            headers=self.auth_headers,
            timeout=5
        )
        
        if response.status_code >= 500:
            print("    ✅ Service is down as expected")
            
            # Wait for recovery
            print("    Waiting for service recovery...")
            time.sleep(12)  # Wait longer than error duration
            
            # Test recovery
            recovery_start = time.time()
            recovery_response = self.session.get(
                f'{self.backend_url}/api/plans',
                headers=self.auth_headers,
                timeout=10
            )
            recovery_duration = time.time() - recovery_start
            
            if recovery_response.status_code == 200:
                print("    ✅ Service recovered successfully")
                self.reporter.add_test_result(
                    'service_recovery',
                    'passed',
                    recovery_duration,
                    {'recovery_status_code': recovery_response.status_code}
                )
            else:
                print(f"    ❌ Service recovery failed: HTTP {recovery_response.status_code}")
                self.reporter.add_test_result(
                    'service_recovery',
                    'failed',
                    recovery_duration,
                    {'recovery_status_code': recovery_response.status_code}
                )
        else:
            print("    ⚠️  Service didn't fail as expected")
            self.reporter.add_test_result(
                'service_recovery',
                'failed',
                time.time() - start_time,
                {'initial_status_code': response.status_code}
            )
    
    def run_all_tests(self):
        """Run all error injection and unhappy path tests"""
        print("💥 Error Injection and Unhappy Path Testing")
        print("=" * 60)
        
        # Setup test user
        print("🔧 Setting up test user...")
        success, user_data = self.setup_test_user()
        if not success:
            print("❌ Failed to setup test user")
            return False
        print(f"✅ Test user created: {user_data['username']}")
        
        # Run error injection tests
        self.test_auth_service_failure()
        self.test_plan_service_timeout()
        self.test_payment_service_unavailable()
        self.test_user_service_failure()
        
        # Run unhappy path tests
        self.test_unhappy_path_scenarios()
        
        # Run cascade failure tests
        self.test_cascade_failures()
        
        # Run recovery tests
        self.test_recovery_scenarios()
        
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
        report_file = self.reporter.export_results('error_injection_report.json')
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return summary['success_rate'] >= 80.0  # Allow some failures in error testing

def main():
    """Main function to run error injection tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run error injection and unhappy path tests')
    parser.add_argument('--backend-url', default='http://127.0.0.1:5000',
                       help='Backend service URL')
    parser.add_argument('--frontend-url', default='http://127.0.0.1:3002',
                       help='Frontend service URL')
    parser.add_argument('--service', choices=['auth', 'plan', 'payment', 'user', 'all'],
                       default='all', help='Specific service to test')
    parser.add_argument('--error-type', choices=['timeout', 'failure', 'unavailable', 'all'],
                       default='all', help='Specific error type to test')
    parser.add_argument('--duration', type=int, default=30,
                       help='Duration of error injection in seconds')
    
    args = parser.parse_args()
    
    # Run tests
    tester = ErrorInjectionTester(args.backend_url, args.frontend_url)
    
    if args.service != 'all' and args.error_type != 'all':
        # Run specific test
        print(f"🎯 Testing {args.service} service with {args.error_type} error...")
        success = tester.inject_service_error(args.service, args.error_type, args.duration)
        time.sleep(args.duration + 5)
        tester.clear_all_errors()
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Error injection tests completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Some error injection tests failed. Check the report for details.")
            sys.exit(1)

if __name__ == '__main__':
    main()
