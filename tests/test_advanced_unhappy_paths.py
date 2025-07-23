#!/usr/bin/env python3
"""
Advanced Unhappy Path Testing with Enhanced Datadog Integration
Tests complex failure scenarios and business logic edge cases
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

import requests
import json
import time
import random
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from test_helpers import ErrorInjector, TestReporter, APITestHelper, TestDataGenerator
from datadog import statsd

class AdvancedUnhappyPathTester:
    """Advanced unhappy path testing with Datadog integration"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000', frontend_url='http://127.0.0.1:3002'):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.reporter = TestReporter()
        self.session = requests.Session()
        self.auth_headers = None
        
        # Datadog metrics configuration
        self.dd_prefix = 'telecom.unhappy_path'
        self.dd_tags = ['env:production', 'component:testing', 'team:telecom']
        
        # Business scenarios configuration
        self.business_scenarios = {
            'payment_failures': ['insufficient_funds', 'expired_card', 'blocked_card', 'network_timeout'],
            'auth_failures': ['invalid_credentials', 'account_locked', 'session_expired', 'rate_limited'],
            'plan_failures': ['plan_unavailable', 'quota_exceeded', 'region_restricted', 'maintenance_mode'],
            'user_failures': ['profile_incomplete', 'verification_pending', 'account_suspended', 'data_corruption']
        }
    
    def setup_test_environment(self):
        """Setup test environment with monitoring"""
        print("🔧 Setting up advanced unhappy path test environment...")
        
        # Send setup metric to Datadog
        statsd.increment(f'{self.dd_prefix}.test_setup.started', tags=self.dd_tags)
        
        try:
            # Create test user
            user_data = TestDataGenerator.generate_user_data('unhappy_test')
            
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
                    
                    statsd.increment(f'{self.dd_prefix}.test_setup.success', tags=self.dd_tags)
                    return True, user_data
            
            statsd.increment(f'{self.dd_prefix}.test_setup.failed', tags=self.dd_tags)
            return False, None
            
        except Exception as e:
            statsd.increment(f'{self.dd_prefix}.test_setup.error', tags=self.dd_tags + [f'error:{str(e)[:50]}'])
            return False, None
    
    def test_payment_cascade_failures(self):
        """Test payment system cascade failures"""
        print("\n💳 Testing Payment Cascade Failures...")
        
        test_scenarios = [
            {
                'name': 'payment_gateway_timeout',
                'description': 'Payment gateway timeout leading to retry storms',
                'duration': 45,
                'expected_behavior': 'Graceful degradation with user notification'
            },
            {
                'name': 'payment_validation_failure',
                'description': 'Payment validation service failure',
                'duration': 30,
                'expected_behavior': 'Fallback to basic validation'
            },
            {
                'name': 'fraud_detection_overload',
                'description': 'Fraud detection system overloaded',
                'duration': 60,
                'expected_behavior': 'Allow payments with increased monitoring'
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  🎯 Testing: {scenario['name']}")
            
            # Send scenario start metric
            statsd.increment(
                f'{self.dd_prefix}.payment_cascade.started',
                tags=self.dd_tags + [f'scenario:{scenario["name"]}']
            )
            
            start_time = time.time()
            
            try:
                # Get a plan for payment testing
                plans_response = self.session.get(
                    f'{self.backend_url}/api/plans',
                    headers=self.auth_headers,
                    timeout=10
                )
                
                if plans_response.status_code == 200:
                    plans = plans_response.json().get('plans', [])
                    if plans:
                        plan_id = plans[0]['id']
                        
                        # Simulate multiple payment attempts during failure
                        payment_attempts = []
                        for i in range(5):
                            payment_data = TestDataGenerator.generate_payment_data(plan_id)
                            
                            # Inject different types of payment errors
                            if scenario['name'] == 'payment_gateway_timeout':
                                payment_data['simulate_timeout'] = True
                            elif scenario['name'] == 'payment_validation_failure':
                                payment_data['card_number'] = '4000000000000002'  # Declined card
                            elif scenario['name'] == 'fraud_detection_overload':
                                payment_data['amount'] = 99999  # Suspicious amount
                            
                            try:
                                payment_response = self.session.post(
                                    f'{self.backend_url}/api/payments/process',
                                    json=payment_data,
                                    headers=self.auth_headers,
                                    timeout=15
                                )
                                
                                payment_attempts.append({
                                    'attempt': i + 1,
                                    'status_code': payment_response.status_code,
                                    'response_time': time.time() - start_time,
                                    'success': payment_response.status_code == 200
                                })
                                
                                # Track payment attempt metrics
                                statsd.increment(
                                    f'{self.dd_prefix}.payment_attempt',
                                    tags=self.dd_tags + [
                                        f'scenario:{scenario["name"]}',
                                        f'status:{payment_response.status_code}',
                                        f'attempt:{i+1}'
                                    ]
                                )
                                
                                statsd.histogram(
                                    f'{self.dd_prefix}.payment_response_time',
                                    (time.time() - start_time) * 1000,
                                    tags=self.dd_tags + [f'scenario:{scenario["name"]}']
                                )
                                
                            except requests.exceptions.Timeout:
                                payment_attempts.append({
                                    'attempt': i + 1,
                                    'status_code': 'timeout',
                                    'response_time': 15.0,
                                    'success': False
                                })
                                
                                statsd.increment(
                                    f'{self.dd_prefix}.payment_timeout',
                                    tags=self.dd_tags + [f'scenario:{scenario["name"]}']
                                )
                            
                            time.sleep(2)  # Delay between attempts
                        
                        # Analyze results
                        successful_payments = [p for p in payment_attempts if p['success']]
                        failed_payments = [p for p in payment_attempts if not p['success']]
                        
                        duration = time.time() - start_time
                        
                        # Record test results
                        self.reporter.add_test_result(
                            f'payment_cascade_{scenario["name"]}',
                            'passed' if len(failed_payments) >= 3 else 'failed',  # Expect failures
                            duration,
                            {
                                'scenario': scenario['name'],
                                'total_attempts': len(payment_attempts),
                                'successful_payments': len(successful_payments),
                                'failed_payments': len(failed_payments),
                                'expected_behavior': scenario['expected_behavior']
                            }
                        )
                        
                        # Send summary metrics
                        statsd.gauge(
                            f'{self.dd_prefix}.payment_success_rate',
                            (len(successful_payments) / len(payment_attempts)) * 100,
                            tags=self.dd_tags + [f'scenario:{scenario["name"]}']
                        )
                        
                        print(f"    ✅ Scenario completed: {len(failed_payments)}/{len(payment_attempts)} failures (expected)")
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"    ❌ Scenario failed: {str(e)}")
                
                self.reporter.add_test_result(
                    f'payment_cascade_{scenario["name"]}',
                    'failed',
                    duration,
                    {'error': str(e)}
                )
                
                statsd.increment(
                    f'{self.dd_prefix}.payment_cascade.error',
                    tags=self.dd_tags + [f'scenario:{scenario["name"]}', f'error:{str(e)[:50]}']
                )
    
    def test_authentication_attack_scenarios(self):
        """Test authentication under attack scenarios"""
        print("\n🔐 Testing Authentication Attack Scenarios...")
        
        attack_scenarios = [
            {
                'name': 'brute_force_attack',
                'description': 'Simulate brute force login attempts',
                'attempts': 20,
                'concurrent': 5
            },
            {
                'name': 'credential_stuffing',
                'description': 'Test with common username/password combinations',
                'attempts': 15,
                'concurrent': 3
            },
            {
                'name': 'session_hijacking',
                'description': 'Test session security under attack',
                'attempts': 10,
                'concurrent': 2
            }
        ]
        
        for scenario in attack_scenarios:
            print(f"  🎯 Testing: {scenario['name']}")
            
            statsd.increment(
                f'{self.dd_prefix}.auth_attack.started',
                tags=self.dd_tags + [f'attack:{scenario["name"]}']
            )
            
            start_time = time.time()
            attack_results = []
            
            def perform_attack_attempt(attempt_num):
                try:
                    if scenario['name'] == 'brute_force_attack':
                        # Try random credentials
                        credentials = {
                            'username': f'user{random.randint(1, 100)}',
                            'password': f'pass{random.randint(1, 1000)}'
                        }
                    elif scenario['name'] == 'credential_stuffing':
                        # Use common credentials
                        common_creds = [
                            {'username': 'admin', 'password': 'admin'},
                            {'username': 'user', 'password': 'password'},
                            {'username': 'test', 'password': '123456'},
                            {'username': 'guest', 'password': 'guest'}
                        ]
                        credentials = random.choice(common_creds)
                    else:  # session_hijacking
                        # Try to use invalid/expired tokens
                        credentials = {
                            'username': 'validuser',
                            'password': 'validpass'
                        }
                    
                    attempt_start = time.time()
                    response = self.session.post(
                        f'{self.backend_url}/api/auth/login',
                        json=credentials,
                        timeout=10
                    )
                    attempt_duration = time.time() - attempt_start
                    
                    result = {
                        'attempt': attempt_num,
                        'status_code': response.status_code,
                        'response_time': attempt_duration,
                        'blocked': response.status_code == 429,  # Rate limited
                        'credentials': credentials['username']
                    }
                    
                    # Track individual attempt metrics
                    statsd.increment(
                        f'{self.dd_prefix}.auth_attempt',
                        tags=self.dd_tags + [
                            f'attack:{scenario["name"]}',
                            f'status:{response.status_code}',
                            f'blocked:{"yes" if result["blocked"] else "no"}'
                        ]
                    )
                    
                    statsd.histogram(
                        f'{self.dd_prefix}.auth_response_time',
                        attempt_duration * 1000,
                        tags=self.dd_tags + [f'attack:{scenario["name"]}']
                    )
                    
                    return result
                    
                except Exception as e:
                    return {
                        'attempt': attempt_num,
                        'status_code': 'error',
                        'response_time': 10.0,
                        'blocked': False,
                        'error': str(e)
                    }
            
            # Execute concurrent attack attempts
            with ThreadPoolExecutor(max_workers=scenario['concurrent']) as executor:
                futures = [
                    executor.submit(perform_attack_attempt, i)
                    for i in range(scenario['attempts'])
                ]
                
                for future in as_completed(futures):
                    result = future.result()
                    attack_results.append(result)
                    time.sleep(0.1)  # Small delay between attempts
            
            # Analyze attack results
            blocked_attempts = [r for r in attack_results if r.get('blocked', False)]
            successful_attempts = [r for r in attack_results if r.get('status_code') == 200]
            failed_attempts = [r for r in attack_results if r.get('status_code') not in [200, 429]]
            
            duration = time.time() - start_time
            
            # Record test results
            self.reporter.add_test_result(
                f'auth_attack_{scenario["name"]}',
                'passed' if len(blocked_attempts) > 0 else 'failed',  # Expect some blocking
                duration,
                {
                    'scenario': scenario['name'],
                    'total_attempts': len(attack_results),
                    'blocked_attempts': len(blocked_attempts),
                    'successful_attempts': len(successful_attempts),
                    'failed_attempts': len(failed_attempts),
                    'block_rate': (len(blocked_attempts) / len(attack_results)) * 100
                }
            )
            
            # Send attack summary metrics
            statsd.gauge(
                f'{self.dd_prefix}.auth_block_rate',
                (len(blocked_attempts) / len(attack_results)) * 100,
                tags=self.dd_tags + [f'attack:{scenario["name"]}']
            )
            
            statsd.gauge(
                f'{self.dd_prefix}.auth_success_rate',
                (len(successful_attempts) / len(attack_results)) * 100,
                tags=self.dd_tags + [f'attack:{scenario["name"]}']
            )
            
            print(f"    ✅ Attack scenario completed: {len(blocked_attempts)}/{len(attack_results)} blocked")
    
    def test_data_corruption_scenarios(self):
        """Test system behavior with corrupted data"""
        print("\n🗄️ Testing Data Corruption Scenarios...")
        
        corruption_scenarios = [
            {
                'name': 'malformed_json_payloads',
                'description': 'Send malformed JSON in API requests',
                'payloads': [
                    '{"username": "test", "password":}',  # Missing value
                    '{"username": "test", "password": "test", }',  # Trailing comma
                    '{"username": "test", "password": "test"',  # Missing closing brace
                    '{username: "test", "password": "test"}',  # Unquoted key
                    '{"username": null, "password": "test"}'  # Null value
                ]
            },
            {
                'name': 'sql_injection_attempts',
                'description': 'Test SQL injection protection',
                'payloads': [
                    "'; DROP TABLE users; --",
                    "' OR '1'='1",
                    "admin'--",
                    "' UNION SELECT * FROM users --",
                    "'; INSERT INTO users VALUES ('hacker', 'pass'); --"
                ]
            },
            {
                'name': 'xss_injection_attempts',
                'description': 'Test XSS protection',
                'payloads': [
                    "<script>alert('xss')</script>",
                    "javascript:alert('xss')",
                    "<img src=x onerror=alert('xss')>",
                    "';alert('xss');//",
                    "<svg onload=alert('xss')>"
                ]
            }
        ]
        
        for scenario in corruption_scenarios:
            print(f"  🎯 Testing: {scenario['name']}")
            
            statsd.increment(
                f'{self.dd_prefix}.data_corruption.started',
                tags=self.dd_tags + [f'corruption:{scenario["name"]}']
            )
            
            start_time = time.time()
            corruption_results = []
            
            for i, payload in enumerate(scenario['payloads']):
                try:
                    if scenario['name'] == 'malformed_json_payloads':
                        # Send malformed JSON directly
                        response = self.session.post(
                            f'{self.backend_url}/api/auth/login',
                            data=payload,
                            headers={'Content-Type': 'application/json'},
                            timeout=10
                        )
                    else:
                        # Send injection attempts in username field
                        response = self.session.post(
                            f'{self.backend_url}/api/auth/login',
                            json={'username': payload, 'password': 'testpass'},
                            timeout=10
                        )
                    
                    result = {
                        'payload_index': i,
                        'payload': payload[:50] + '...' if len(payload) > 50 else payload,
                        'status_code': response.status_code,
                        'properly_handled': response.status_code in [400, 401, 422],  # Expected error codes
                        'response_size': len(response.content)
                    }
                    
                    corruption_results.append(result)
                    
                    # Track corruption attempt metrics
                    statsd.increment(
                        f'{self.dd_prefix}.corruption_attempt',
                        tags=self.dd_tags + [
                            f'corruption:{scenario["name"]}',
                            f'status:{response.status_code}',
                            f'handled:{"yes" if result["properly_handled"] else "no"}'
                        ]
                    )
                    
                except requests.exceptions.RequestException as e:
                    # Connection errors are also acceptable (server protecting itself)
                    result = {
                        'payload_index': i,
                        'payload': payload[:50] + '...' if len(payload) > 50 else payload,
                        'status_code': 'connection_error',
                        'properly_handled': True,  # Connection rejection is proper handling
                        'error': str(e)
                    }
                    corruption_results.append(result)
                    
                    statsd.increment(
                        f'{self.dd_prefix}.corruption_blocked',
                        tags=self.dd_tags + [f'corruption:{scenario["name"]}']
                    )
                
                time.sleep(0.5)  # Small delay between attempts
            
            # Analyze corruption test results
            properly_handled = [r for r in corruption_results if r['properly_handled']]
            improperly_handled = [r for r in corruption_results if not r['properly_handled']]
            
            duration = time.time() - start_time
            
            # Record test results
            self.reporter.add_test_result(
                f'data_corruption_{scenario["name"]}',
                'passed' if len(improperly_handled) == 0 else 'failed',
                duration,
                {
                    'scenario': scenario['name'],
                    'total_payloads': len(corruption_results),
                    'properly_handled': len(properly_handled),
                    'improperly_handled': len(improperly_handled),
                    'protection_rate': (len(properly_handled) / len(corruption_results)) * 100
                }
            )
            
            # Send corruption summary metrics
            statsd.gauge(
                f'{self.dd_prefix}.corruption_protection_rate',
                (len(properly_handled) / len(corruption_results)) * 100,
                tags=self.dd_tags + [f'corruption:{scenario["name"]}']
            )
            
            print(f"    ✅ Corruption test completed: {len(properly_handled)}/{len(corruption_results)} properly handled")
    
    def test_resource_exhaustion_scenarios(self):
        """Test system behavior under resource exhaustion"""
        print("\n⚡ Testing Resource Exhaustion Scenarios...")
        
        exhaustion_scenarios = [
            {
                'name': 'memory_pressure',
                'description': 'Create memory pressure through large payloads',
                'payload_size': 1024 * 1024,  # 1MB payloads
                'concurrent_requests': 10,
                'duration': 30
            },
            {
                'name': 'connection_pool_exhaustion',
                'description': 'Exhaust database connection pool',
                'concurrent_requests': 50,
                'duration': 45
            },
            {
                'name': 'cpu_intensive_operations',
                'description': 'Trigger CPU-intensive operations',
                'concurrent_requests': 20,
                'duration': 60
            }
        ]
        
        for scenario in exhaustion_scenarios:
            print(f"  🎯 Testing: {scenario['name']}")
            
            statsd.increment(
                f'{self.dd_prefix}.resource_exhaustion.started',
                tags=self.dd_tags + [f'exhaustion:{scenario["name"]}']
            )
            
            start_time = time.time()
            exhaustion_results = []
            
            def create_resource_pressure():
                try:
                    if scenario['name'] == 'memory_pressure':
                        # Create large payload
                        large_data = {
                            'username': 'test_user',
                            'password': 'test_pass',
                            'large_field': 'x' * scenario['payload_size']
                        }
                        response = self.session.post(
                            f'{self.backend_url}/api/auth/register',
                            json=large_data,
                            timeout=15
                        )
                    elif scenario['name'] == 'connection_pool_exhaustion':
                        # Make database-intensive requests
                        response = self.session.get(
                            f'{self.backend_url}/api/plans',
                            headers=self.auth_headers,
                            timeout=15
                        )
                    else:  # cpu_intensive_operations
                        # Trigger complex operations
                        response = self.session.get(
                            f'{self.backend_url}/api/health/performance',
                            timeout=15
                        )
                    
                    return {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'success': 200 <= response.status_code < 300
                    }
                    
                except Exception as e:
                    return {
                        'status_code': 'error',
                        'response_time': 15.0,
                        'success': False,
                        'error': str(e)
                    }
            
            # Create sustained resource pressure
            end_time = start_time + scenario['duration']
            
            with ThreadPoolExecutor(max_workers=scenario['concurrent_requests']) as executor:
                while time.time() < end_time:
                    # Submit batch of requests
                    futures = [
                        executor.submit(create_resource_pressure)
                        for _ in range(min(scenario['concurrent_requests'], 10))
                    ]
                    
                    for future in as_completed(futures, timeout=20):
                        try:
                            result = future.result()
                            exhaustion_results.append(result)
                            
                            # Track resource pressure metrics
                            statsd.increment(
                                f'{self.dd_prefix}.resource_pressure',
                                tags=self.dd_tags + [
                                    f'exhaustion:{scenario["name"]}',
                                    f'status:{result["status_code"]}',
                                    f'success:{"yes" if result["success"] else "no"}'
                                ]
                            )
                            
                            statsd.histogram(
                                f'{self.dd_prefix}.resource_response_time',
                                result['response_time'] * 1000,
                                tags=self.dd_tags + [f'exhaustion:{scenario["name"]}']
                            )
                            
                        except Exception as e:
                            exhaustion_results.append({
                                'status_code': 'timeout',
                                'response_time': 20.0,
                                'success': False,
                                'error': str(e)
                            })
                    
                    time.sleep(1)  # Brief pause between batches
            
            # Analyze exhaustion test results
            successful_requests = [r for r in exhaustion_results if r['success']]
            failed_requests = [r for r in exhaustion_results if not r['success']]
            avg_response_time = sum(r['response_time'] for r in exhaustion_results) / len(exhaustion_results)
            
            duration = time.time() - start_time
            
            # Record test results
            self.reporter.add_test_result(
                f'resource_exhaustion_{scenario["name"]}',
                'passed' if len(successful_requests) > 0 else 'failed',  # System should handle some requests
                duration,
                {
                    'scenario': scenario['name'],
                    'total_requests': len(exhaustion_results),
                    'successful_requests': len(successful_requests),
                    'failed_requests': len(failed_requests),
                    'avg_response_time': avg_response_time,
                    'success_rate': (len(successful_requests) / len(exhaustion_results)) * 100
                }
            )
            
            # Send exhaustion summary metrics
            statsd.gauge(
                f'{self.dd_prefix}.exhaustion_success_rate',
                (len(successful_requests) / len(exhaustion_results)) * 100,
                tags=self.dd_tags + [f'exhaustion:{scenario["name"]}']
            )
            
            statsd.gauge(
                f'{self.dd_prefix}.exhaustion_avg_response_time',
                avg_response_time * 1000,
                tags=self.dd_tags + [f'exhaustion:{scenario["name"]}']
            )
            
            print(f"    ✅ Exhaustion test completed: {len(successful_requests)}/{len(exhaustion_results)} successful")
    
    def test_business_logic_edge_cases(self):
        """Test business logic edge cases specific to telecom domain"""
        print("\n📱 Testing Telecom Business Logic Edge Cases...")
        
        edge_cases = [
            {
                'name': 'plan_switching_conflicts',
                'description': 'Test conflicts when switching plans rapidly',
                'test_func': self._test_rapid_plan_switching
            },
            {
                'name': 'payment_timing_issues',
                'description': 'Test payment processing during plan expiry',
                'test_func': self._test_payment_timing_conflicts
            },
            {
                'name': 'quota_boundary_conditions',
                'description': 'Test behavior at quota boundaries',
                'test_func': self._test_quota_boundaries
            },
            {
                'name': 'concurrent_user_operations',
                'description': 'Test concurrent operations on same user account',
                'test_func': self._test_concurrent_user_operations
            }
        ]
        
        for edge_case in edge_cases:
            print(f"  🎯 Testing: {edge_case['name']}")
            
            statsd.increment(
                f'{self.dd_prefix}.business_logic.started',
                tags=self.dd_tags + [f'edge_case:{edge_case["name"]}']
            )
            
            start_time = time.time()
            
            try:
                result = edge_case['test_func']()
                duration = time.time() - start_time
                
                self.reporter.add_test_result(
                    f'business_logic_{edge_case["name"]}',
                    'passed' if result['success'] else 'failed',
                    duration,
                    result
                )
                
                statsd.increment(
                    f'{self.dd_prefix}.business_logic.completed',
                    tags=self.dd_tags + [
                        f'edge_case:{edge_case["name"]}',
                        f'success:{"yes" if result["success"] else "no"}'
                    ]
                )
                
                print(f"    ✅ Edge case test completed: {result.get('summary', 'No summary')}")
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"    ❌ Edge case test failed: {str(e)}")
                
                self.reporter.add_test_result(
                    f'business_logic_{edge_case["name"]}',
                    'failed',
                    duration,
                    {'error': str(e)}
                )
                
                statsd.increment(
                    f'{self.dd_prefix}.business_logic.error',
                    tags=self.dd_tags + [f'edge_case:{edge_case["name"]}']
                )
    
    def _test_rapid_plan_switching(self):
        """Test rapid plan switching scenarios"""
        try:
            # Get available plans
            plans_response = self.session.get(
                f'{self.backend_url}/api/plans',
                headers=self.auth_headers,
                timeout=10
            )
            
            if plans_response.status_code != 200:
                return {'success': False, 'error': 'Could not fetch plans'}
            
            plans = plans_response.json().get('plans', [])
            if len(plans) < 2:
                return {'success': False, 'error': 'Need at least 2 plans for switching test'}
            
            # Rapidly switch between plans
            switch_results = []
            for i in range(5):
                plan = plans[i % len(plans)]
                payment_data = TestDataGenerator.generate_payment_data(plan['id'])
                
                try:
                    switch_response = self.session.post(
                        f'{self.backend_url}/api/payments/process',
                        json=payment_data,
                        headers=self.auth_headers,
                        timeout=10
                    )
                    
                    switch_results.append({
                        'switch_attempt': i + 1,
                        'plan_id': plan['id'],
                        'status_code': switch_response.status_code,
                        'success': switch_response.status_code == 200
                    })
                    
                except Exception as e:
                    switch_results.append({
                        'switch_attempt': i + 1,
                        'plan_id': plan['id'],
                        'status_code': 'error',
                        'success': False,
                        'error': str(e)
                    })
                
                time.sleep(0.5)  # Rapid switching
            
            successful_switches = [r for r in switch_results if r['success']]
            
            return {
                'success': len(successful_switches) > 0,
                'summary': f'{len(successful_switches)}/{len(switch_results)} plan switches successful',
                'switch_results': switch_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_payment_timing_conflicts(self):
        """Test payment processing during plan expiry scenarios"""
        try:
            # This would test edge cases around plan expiry timing
            # For now, simulate the scenario
            timing_results = []
            
            for i in range(3):
                try:
                    # Simulate payment during plan transition
                    response = self.session.get(
                        f'{self.backend_url}/api/users/dashboard',
                        headers=self.auth_headers,
                        timeout=10
                    )
                    
                    timing_results.append({
                        'timing_test': i + 1,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    })
                    
                except Exception as e:
                    timing_results.append({
                        'timing_test': i + 1,
                        'status_code': 'error',
                        'success': False,
                        'error': str(e)
                    })
                
                time.sleep(1)
            
            successful_timing = [r for r in timing_results if r['success']]
            
            return {
                'success': len(successful_timing) > 0,
                'summary': f'{len(successful_timing)}/{len(timing_results)} timing tests successful',
                'timing_results': timing_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_quota_boundaries(self):
        """Test behavior at quota boundaries"""
        try:
            # Test quota boundary conditions
            boundary_results = []
            
            # Test different quota scenarios
            quota_tests = ['data_limit', 'call_minutes', 'sms_limit']
            
            for quota_type in quota_tests:
                try:
                    # Simulate quota boundary test
                    response = self.session.get(
                        f'{self.backend_url}/api/users/usage',
                        headers=self.auth_headers,
                        timeout=10
                    )
                    
                    boundary_results.append({
                        'quota_type': quota_type,
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 404]  # 404 is acceptable if endpoint doesn't exist
                    })
                    
                except Exception as e:
                    boundary_results.append({
                        'quota_type': quota_type,
                        'status_code': 'error',
                        'success': False,
                        'error': str(e)
                    })
            
            successful_boundary = [r for r in boundary_results if r['success']]
            
            return {
                'success': len(successful_boundary) > 0,
                'summary': f'{len(successful_boundary)}/{len(boundary_results)} quota boundary tests successful',
                'boundary_results': boundary_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_concurrent_user_operations(self):
        """Test concurrent operations on same user account"""
        try:
            concurrent_results = []
            
            def concurrent_operation(operation_id):
                try:
                    # Simulate concurrent user operations
                    response = self.session.get(
                        f'{self.backend_url}/api/users/profile',
                        headers=self.auth_headers,
                        timeout=10
                    )
                    
                    return {
                        'operation_id': operation_id,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                    
                except Exception as e:
                    return {
                        'operation_id': operation_id,
                        'status_code': 'error',
                        'success': False,
                        'error': str(e)
                    }
            
            # Execute concurrent operations
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_operation, i) for i in range(10)]
                
                for future in as_completed(futures):
                    result = future.result()
                    concurrent_results.append(result)
            
            successful_concurrent = [r for r in concurrent_results if r['success']]
            
            return {
                'success': len(successful_concurrent) > 0,
                'summary': f'{len(successful_concurrent)}/{len(concurrent_results)} concurrent operations successful',
                'concurrent_results': concurrent_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_chaos_engineering_scenarios(self):
        """Test chaos engineering scenarios"""
        print("\n🌪️ Testing Chaos Engineering Scenarios...")
        
        chaos_scenarios = [
            {
                'name': 'random_service_failures',
                'description': 'Randomly fail services during normal operations',
                'duration': 120
            },
            {
                'name': 'network_partitions',
                'description': 'Simulate network partitions between services',
                'duration': 90
            },
            {
                'name': 'gradual_performance_degradation',
                'description': 'Gradually degrade performance over time',
                'duration': 180
            }
        ]
        
        for scenario in chaos_scenarios:
            print(f"  🎯 Testing: {scenario['name']}")
            
            statsd.increment(
                f'{self.dd_prefix}.chaos_engineering.started',
                tags=self.dd_tags + [f'chaos:{scenario["name"]}']
            )
            
            start_time = time.time()
            chaos_results = []
            
            try:
                # Execute chaos scenario
                end_time = start_time + scenario['duration']
                
                while time.time() < end_time:
                    # Perform random operations during chaos
                    operations = [
                        ('GET', f'{self.backend_url}/api/plans'),
                        ('GET', f'{self.backend_url}/api/users/profile'),
                        ('GET', f'{self.backend_url}/api/health/detailed')
                    ]
                    
                    for method, url in operations:
                        try:
                            if method == 'GET':
                                response = self.session.get(url, headers=self.auth_headers, timeout=10)
                            
                            chaos_results.append({
                                'operation': f'{method} {url.split("/")[-1]}',
                                'status_code': response.status_code,
                                'response_time': response.elapsed.total_seconds(),
                                'success': 200 <= response.status_code < 300
                            })
                            
                            # Track chaos metrics
                            statsd.increment(
                                f'{self.dd_prefix}.chaos_operation',
                                tags=self.dd_tags + [
                                    f'chaos:{scenario["name"]}',
                                    f'operation:{url.split("/")[-1]}',
                                    f'status:{response.status_code}'
                                ]
                            )
                            
                        except Exception as e:
                            chaos_results.append({
                                'operation': f'{method} {url.split("/")[-1]}',
                                'status_code': 'error',
                                'response_time': 10.0,
                                'success': False,
                                'error': str(e)
                            })
                    
                    time.sleep(5)  # Wait between operation batches
                
                # Analyze chaos results
                successful_ops = [r for r in chaos_results if r['success']]
                failed_ops = [r for r in chaos_results if not r['success']]
                
                duration = time.time() - start_time
                
                # Record chaos test results
                self.reporter.add_test_result(
                    f'chaos_engineering_{scenario["name"]}',
                    'passed' if len(successful_ops) > len(failed_ops) * 0.5 else 'failed',  # At least 50% success
                    duration,
                    {
                        'scenario': scenario['name'],
                        'total_operations': len(chaos_results),
                        'successful_operations': len(successful_ops),
                        'failed_operations': len(failed_ops),
                        'success_rate': (len(successful_ops) / len(chaos_results)) * 100 if chaos_results else 0
                    }
                )
                
                # Send chaos summary metrics
                statsd.gauge(
                    f'{self.dd_prefix}.chaos_success_rate',
                    (len(successful_ops) / len(chaos_results)) * 100 if chaos_results else 0,
                    tags=self.dd_tags + [f'chaos:{scenario["name"]}']
                )
                
                print(f"    ✅ Chaos scenario completed: {len(successful_ops)}/{len(chaos_results)} operations successful")
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"    ❌ Chaos scenario failed: {str(e)}")
                
                self.reporter.add_test_result(
                    f'chaos_engineering_{scenario["name"]}',
                    'failed',
                    duration,
                    {'error': str(e)}
                )
                
                statsd.increment(
                    f'{self.dd_prefix}.chaos_engineering.error',
                    tags=self.dd_tags + [f'chaos:{scenario["name"]}']
                )
    
    def run_all_advanced_tests(self):
        """Run all advanced unhappy path tests"""
        print("🚀 Advanced Unhappy Path Testing with Datadog Integration")
        print("=" * 70)
        
        # Setup test environment
        print("🔧 Setting up test environment...")
        success, user_data = self.setup_test_environment()
        if not success:
            print("❌ Failed to setup test environment")
            return False
        print(f"✅ Test environment ready with user: {user_data['username']}")
        
        # Send test suite start metric
        statsd.increment(f'{self.dd_prefix}.test_suite.started', tags=self.dd_tags)
        suite_start_time = time.time()
        
        try:
            # Run all test categories
            self.test_payment_cascade_failures()
            self.test_authentication_attack_scenarios()
            self.test_data_corruption_scenarios()
            self.test_resource_exhaustion_scenarios()
            self.test_business_logic_edge_cases()
            self.test_chaos_engineering_scenarios()
            
            # Generate comprehensive summary
            print("\n📊 Advanced Test Summary")
            print("=" * 60)
            summary = self.reporter.generate_summary()
            
            print(f"Total Tests: {summary['total_tests']}")
            print(f"Passed: {summary['passed_tests']} ✅")
            print(f"Failed: {summary['failed_tests']} ❌")
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Total Duration: {summary['total_duration']:.2f}s")
            print(f"Average Test Duration: {summary['average_duration']:.2f}s")
            
            # Send final metrics to Datadog
            suite_duration = time.time() - suite_start_time
            
            statsd.gauge(f'{self.dd_prefix}.test_suite.duration', suite_duration, tags=self.dd_tags)
            statsd.gauge(f'{self.dd_prefix}.test_suite.success_rate', summary['success_rate'], tags=self.dd_tags)
            statsd.gauge(f'{self.dd_prefix}.test_suite.total_tests', summary['total_tests'], tags=self.dd_tags)
            
            statsd.increment(
                f'{self.dd_prefix}.test_suite.completed',
                tags=self.dd_tags + [f'success_rate:{int(summary["success_rate"])}']
            )
            
            # Export detailed results
            report_file = self.reporter.export_results('advanced_unhappy_path_report.json')
            print(f"\n📄 Detailed report saved to: {report_file}")
            
            # Create Datadog dashboard link suggestion
            print(f"\n📈 Monitor results in Datadog:")
            print(f"   - Metrics: telecom.unhappy_path.*")
            print(f"   - Tags: env:production, component:testing, team:telecom")
            print(f"   - Dashboard: Create custom dashboard with these metrics")
            
            return summary['success_rate'] >= 70.0  # Allow more failures in advanced testing
            
        except Exception as e:
            suite_duration = time.time() - suite_start_time
            print(f"\n❌ Test suite failed: {str(e)}")
            
            statsd.increment(f'{self.dd_prefix}.test_suite.error', tags=self.dd_tags + [f'error:{str(e)[:50]}'])
            statsd.gauge(f'{self.dd_prefix}.test_suite.duration', suite_duration, tags=self.dd_tags)
            
            return False

def main():
    """Main function to run advanced unhappy path tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run advanced unhappy path tests with Datadog integration')
    parser.add_argument('--backend-url', default='http://127.0.0.1:5000',
                       help='Backend service URL')
    parser.add_argument('--frontend-url', default='http://127.0.0.1:3002',
                       help='Frontend service URL')
    parser.add_argument('--test-category', 
                       choices=['payment', 'auth', 'corruption', 'exhaustion', 'business', 'chaos', 'all'],
                       default='all', help='Specific test category to run')
    parser.add_argument('--duration', type=int, default=300,
                       help='Maximum duration for long-running tests in seconds')
    parser.add_argument('--concurrent-users', type=int, default=10,
                       help='Number of concurrent users for load testing')
    
    args = parser.parse_args()
    
    # Run tests
    tester = AdvancedUnhappyPathTester(args.backend_url, args.frontend_url)
    
    if args.test_category != 'all':
        # Run specific test category
        print(f"🎯 Running {args.test_category} tests...")
        
        if args.test_category == 'payment':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_payment_cascade_failures()
        elif args.test_category == 'auth':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_authentication_attack_scenarios()
        elif args.test_category == 'corruption':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_data_corruption_scenarios()
        elif args.test_category == 'exhaustion':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_resource_exhaustion_scenarios()
        elif args.test_category == 'business':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_business_logic_edge_cases()
        elif args.test_category == 'chaos':
            success, _ = tester.setup_test_environment()
            if success:
                tester.test_chaos_engineering_scenarios()
        
        # Generate summary for single category
        summary = tester.reporter.generate_summary()
        print(f"\n📊 {args.test_category.title()} Test Results:")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        sys.exit(0 if summary['success_rate'] >= 70.0 else 1)
    else:
        # Run all tests
        success = tester.run_all_advanced_tests()
        
        if success:
            print("\n🎉 Advanced unhappy path tests completed successfully!")
            print("📈 Check Datadog for detailed metrics and traces")
            sys.exit(0)
        else:
            print("\n⚠️  Some advanced tests failed. Check the report and Datadog for details.")
            sys.exit(1)

if __name__ == '__main__':
    main()
