#!/usr/bin/env python3
"""
End-to-End Happy Path Test Script
Tests the complete user journey from registration to plan subscription
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

import requests
import json
import time
from datetime import datetime
from test_helpers import APITestHelper, TestDataGenerator, TestReporter

class E2EHappyPathTester:
    """End-to-end happy path testing"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000', frontend_url='http://127.0.0.1:3002'):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.reporter = TestReporter()
        self.session = requests.Session()
        
    def test_user_registration(self):
        """Test user registration"""
        print("👤 Testing User Registration...")
        start_time = time.time()
        
        user_data = TestDataGenerator.generate_user_data('e2e_user')
        
        try:
            response = self.session.post(
                f'{self.backend_url}/api/auth/register',
                json=user_data,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 201:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ User registered successfully: {user_data['username']}")
                    self.reporter.add_test_result(
                        'user_registration',
                        'passed',
                        duration,
                        {'username': user_data['username']}
                    )
                    return True, user_data
                else:
                    print(f"  ❌ Registration failed: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'user_registration',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Registration failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'user_registration',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Registration error: {str(e)}")
            self.reporter.add_test_result(
                'user_registration',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_user_login(self, user_data):
        """Test user login"""
        print("🔐 Testing User Login...")
        start_time = time.time()
        
        login_data = {
            'username': user_data['username'],
            'password': user_data['password']
        }
        
        try:
            response = self.session.post(
                f'{self.backend_url}/api/auth/login',
                json=login_data,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'access_token' in result:
                    print(f"  ✅ User logged in successfully")
                    self.auth_headers = {'Authorization': f'Bearer {result["access_token"]}'}
                    self.reporter.add_test_result(
                        'user_login',
                        'passed',
                        duration,
                        {'has_token': True}
                    )
                    return True, result
                else:
                    print(f"  ❌ Login failed: {result.get('error', 'No access token')}")
                    self.reporter.add_test_result(
                        'user_login',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Login failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'user_login',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Login error: {str(e)}")
            self.reporter.add_test_result(
                'user_login',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_browse_plans(self):
        """Test browsing available plans"""
        print("📋 Testing Plan Browsing...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.backend_url}/api/plans',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'plans' in result:
                    plans = result['plans']
                    if len(plans) > 0:
                        print(f"  ✅ Found {len(plans)} available plans")
                        self.reporter.add_test_result(
                            'browse_plans',
                            'passed',
                            duration,
                            {'plans_count': len(plans)}
                        )
                        return True, plans
                    else:
                        print(f"  ❌ No plans available")
                        self.reporter.add_test_result(
                            'browse_plans',
                            'failed',
                            duration,
                            {'error': 'No plans available'}
                        )
                        return False, None
                else:
                    print(f"  ❌ Failed to get plans: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'browse_plans',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Plans request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'browse_plans',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Browse plans error: {str(e)}")
            self.reporter.add_test_result(
                'browse_plans',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_plan_details(self, plan_id):
        """Test getting plan details"""
        print(f"📄 Testing Plan Details (ID: {plan_id})...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.backend_url}/api/plans/{plan_id}',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'plan' in result:
                    plan = result['plan']
                    print(f"  ✅ Plan details retrieved: {plan.get('name', 'Unknown')}")
                    self.reporter.add_test_result(
                        'plan_details',
                        'passed',
                        duration,
                        {'plan_name': plan.get('name')}
                    )
                    return True, plan
                else:
                    print(f"  ❌ Failed to get plan details: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'plan_details',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Plan details request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'plan_details',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Plan details error: {str(e)}")
            self.reporter.add_test_result(
                'plan_details',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_payment_processing(self, plan_id):
        """Test payment processing"""
        print("💳 Testing Payment Processing...")
        start_time = time.time()
        
        payment_data = TestDataGenerator.generate_payment_data(plan_id)
        
        try:
            response = self.session.post(
                f'{self.backend_url}/api/payments/process',
                json=payment_data,
                headers=self.auth_headers,
                timeout=15
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'transaction_id' in result:
                    transaction_id = result['transaction_id']
                    print(f"  ✅ Payment processed successfully (Transaction: {transaction_id})")
                    self.reporter.add_test_result(
                        'payment_processing',
                        'passed',
                        duration,
                        {'transaction_id': transaction_id}
                    )
                    return True, result
                else:
                    print(f"  ❌ Payment failed: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'payment_processing',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Payment request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'payment_processing',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Payment processing error: {str(e)}")
            self.reporter.add_test_result(
                'payment_processing',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_subscription_verification(self, plan_id):
        """Test subscription verification"""
        print("✅ Testing Subscription Verification...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.backend_url}/api/users/current-plan',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'plan' in result:
                    current_plan = result['plan']
                    if current_plan.get('id') == plan_id:
                        print(f"  ✅ Subscription verified: {current_plan.get('name', 'Unknown')}")
                        self.reporter.add_test_result(
                            'subscription_verification',
                            'passed',
                            duration,
                            {'plan_name': current_plan.get('name')}
                        )
                        return True, current_plan
                    else:
                        print(f"  ❌ Wrong plan subscribed: expected {plan_id}, got {current_plan.get('id')}")
                        self.reporter.add_test_result(
                            'subscription_verification',
                            'failed',
                            duration,
                            {'error': 'Plan mismatch'}
                        )
                        return False, None
                else:
                    print(f"  ❌ No active subscription found")
                    self.reporter.add_test_result(
                        'subscription_verification',
                        'failed',
                        duration,
                        {'error': 'No active subscription'}
                    )
                    return False, None
            else:
                print(f"  ❌ Subscription check failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'subscription_verification',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Subscription verification error: {str(e)}")
            self.reporter.add_test_result(
                'subscription_verification',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_dashboard_access(self):
        """Test dashboard access"""
        print("📊 Testing Dashboard Access...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.backend_url}/api/users/dashboard',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'dashboard' in result:
                    dashboard = result['dashboard']
                    print(f"  ✅ Dashboard accessed successfully")
                    self.reporter.add_test_result(
                        'dashboard_access',
                        'passed',
                        duration,
                        {'has_current_plan': 'current_plan' in dashboard}
                    )
                    return True, dashboard
                else:
                    print(f"  ❌ Dashboard access failed: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'dashboard_access',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Dashboard request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'dashboard_access',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Dashboard access error: {str(e)}")
            self.reporter.add_test_result(
                'dashboard_access',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def test_payment_history(self):
        """Test payment history access"""
        print("📜 Testing Payment History...")
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.backend_url}/api/users/payment-history',
                headers=self.auth_headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'transactions' in result:
                    transactions = result['transactions']
                    print(f"  ✅ Payment history retrieved: {len(transactions)} transactions")
                    self.reporter.add_test_result(
                        'payment_history',
                        'passed',
                        duration,
                        {'transactions_count': len(transactions)}
                    )
                    return True, transactions
                else:
                    print(f"  ❌ Payment history failed: {result.get('error', 'Unknown error')}")
                    self.reporter.add_test_result(
                        'payment_history',
                        'failed',
                        duration,
                        {'error': result.get('error')}
                    )
                    return False, None
            else:
                print(f"  ❌ Payment history request failed with HTTP {response.status_code}")
                self.reporter.add_test_result(
                    'payment_history',
                    'failed',
                    duration,
                    {'status_code': response.status_code}
                )
                return False, None
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Payment history error: {str(e)}")
            self.reporter.add_test_result(
                'payment_history',
                'failed',
                duration,
                {'error': str(e)}
            )
            return False, None
    
    def run_complete_journey(self):
        """Run the complete end-to-end user journey"""
        print("🚀 Starting End-to-End Happy Path Test...")
        print("=" * 60)
        
        # Step 1: User Registration
        success, user_data = self.test_user_registration()
        if not success:
            return False
        
        # Step 2: User Login
        success, login_result = self.test_user_login(user_data)
        if not success:
            return False
        
        # Step 3: Browse Plans
        success, plans = self.test_browse_plans()
        if not success:
            return False
        
        # Step 4: Get Plan Details
        selected_plan = plans[0]  # Select first available plan
        plan_id = selected_plan['id']
        success, plan_details = self.test_plan_details(plan_id)
        if not success:
            return False
        
        # Step 5: Process Payment
        success, payment_result = self.test_payment_processing(plan_id)
        if not success:
            return False
        
        # Step 6: Verify Subscription
        success, subscription = self.test_subscription_verification(plan_id)
        if not success:
            return False
        
        # Step 7: Access Dashboard
        success, dashboard = self.test_dashboard_access()
        if not success:
            return False
        
        # Step 8: Check Payment History
        success, history = self.test_payment_history()
        if not success:
            return False
        
        print("\n🎉 Complete user journey successful!")
        return True
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🧪 End-to-End Happy Path Testing")
        print("=" * 60)
        
        # Run complete journey
        journey_success = self.run_complete_journey()
        
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
        report_file = self.reporter.export_results('e2e_happy_path_report.json')
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return journey_success and summary['success_rate'] == 100.0

def main():
    """Main function to run end-to-end happy path tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run end-to-end happy path tests')
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
    tester = E2EHappyPathTester(args.backend_url, args.frontend_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All end-to-end tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some end-to-end tests failed. Check the report for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
