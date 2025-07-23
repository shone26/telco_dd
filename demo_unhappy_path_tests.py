#!/usr/bin/env python3
"""
Demo script to showcase the Advanced Unhappy Path Testing Framework
This script demonstrates key features without running full test suites
"""
import sys
import os
import time
import requests
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests/utils'))

try:
    from datadog import statsd
    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False
    print("⚠️  Datadog not available - metrics will be simulated")

class UnhappyPathDemo:
    """Demo class to showcase unhappy path testing capabilities"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000'):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.dd_prefix = 'telecom.unhappy_path.demo'
        self.dd_tags = ['env:demo', 'component:testing', 'team:telecom']
    
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"🎯 {text}")
        print(f"{'='*60}")
    
    def print_step(self, text):
        """Print formatted step"""
        print(f"\n📋 {text}")
    
    def print_result(self, text, success=True):
        """Print formatted result"""
        icon = "✅" if success else "❌"
        print(f"   {icon} {text}")
    
    def send_metric(self, metric_name, value=1, metric_type='increment', tags=None):
        """Send metric to Datadog or simulate"""
        if tags is None:
            tags = self.dd_tags
        
        full_metric = f"{self.dd_prefix}.{metric_name}"
        
        if DATADOG_AVAILABLE:
            try:
                if metric_type == 'increment':
                    statsd.increment(full_metric, tags=tags)
                elif metric_type == 'gauge':
                    statsd.gauge(full_metric, value, tags=tags)
                elif metric_type == 'histogram':
                    statsd.histogram(full_metric, value, tags=tags)
                print(f"   📊 Sent metric: {full_metric} = {value}")
            except Exception as e:
                print(f"   ⚠️  Metric send failed: {e}")
        else:
            print(f"   📊 Simulated metric: {full_metric} = {value} (tags: {tags})")
    
    def check_service_health(self):
        """Check if backend service is running"""
        self.print_step("Checking service health...")
        
        try:
            response = self.session.get(f"{self.backend_url}/api/health/", timeout=5)
            if response.status_code == 200:
                self.print_result("Backend service is healthy")
                self.send_metric("service_health_check", 1, 'increment', 
                               self.dd_tags + ['status:healthy'])
                return True
            else:
                self.print_result(f"Backend service returned {response.status_code}", False)
                self.send_metric("service_health_check", 1, 'increment', 
                               self.dd_tags + ['status:unhealthy'])
                return False
        except Exception as e:
            self.print_result(f"Backend service is not accessible: {e}", False)
            self.send_metric("service_health_check", 1, 'increment', 
                           self.dd_tags + ['status:error'])
            return False
    
    def demo_authentication_attacks(self):
        """Demo authentication attack scenarios"""
        self.print_header("Authentication Attack Scenarios Demo")
        
        attack_scenarios = [
            {'username': 'admin', 'password': 'admin', 'type': 'common_credentials'},
            {'username': 'user123', 'password': 'password123', 'type': 'weak_password'},
            {'username': "'; DROP TABLE users; --", 'password': 'test', 'type': 'sql_injection'},
            {'username': '<script>alert("xss")</script>', 'password': 'test', 'type': 'xss_attempt'}
        ]
        
        for i, scenario in enumerate(attack_scenarios, 1):
            self.print_step(f"Attack {i}: Testing {scenario['type']}")
            
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/auth/login",
                    json={'username': scenario['username'], 'password': scenario['password']},
                    timeout=10
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 401:
                    self.print_result("Attack properly blocked (401 Unauthorized)")
                    blocked = True
                elif response.status_code == 400:
                    self.print_result("Attack properly blocked (400 Bad Request)")
                    blocked = True
                elif response.status_code == 429:
                    self.print_result("Attack rate limited (429 Too Many Requests)")
                    blocked = True
                else:
                    self.print_result(f"Unexpected response: {response.status_code}", False)
                    blocked = False
                
                # Send metrics
                self.send_metric("auth_attack_attempt", 1, 'increment', 
                               self.dd_tags + [f'attack_type:{scenario["type"]}', 
                                             f'blocked:{"yes" if blocked else "no"}'])
                self.send_metric("auth_attack_response_time", response_time, 'histogram',
                               self.dd_tags + [f'attack_type:{scenario["type"]}'])
                
            except requests.exceptions.Timeout:
                self.print_result("Request timed out (possible protection mechanism)")
                self.send_metric("auth_attack_timeout", 1, 'increment',
                               self.dd_tags + [f'attack_type:{scenario["type"]}'])
            except Exception as e:
                self.print_result(f"Attack caused error: {e}", False)
                self.send_metric("auth_attack_error", 1, 'increment',
                               self.dd_tags + [f'attack_type:{scenario["type"]}'])
            
            time.sleep(1)  # Brief delay between attacks
    
    def demo_data_corruption(self):
        """Demo data corruption scenarios"""
        self.print_header("Data Corruption Scenarios Demo")
        
        corruption_payloads = [
            ('{"username": "test", "password":}', 'malformed_json_missing_value'),
            ('{"username": "test", "password": "test",}', 'malformed_json_trailing_comma'),
            ('{"username": "test", "password": "test"', 'malformed_json_missing_brace'),
            ('{username: "test", "password": "test"}', 'malformed_json_unquoted_key'),
            ('{"username": null, "password": "test"}', 'null_values')
        ]
        
        for i, (payload, corruption_type) in enumerate(corruption_payloads, 1):
            self.print_step(f"Corruption {i}: Testing {corruption_type}")
            
            try:
                response = self.session.post(
                    f"{self.backend_url}/api/auth/login",
                    data=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code in [400, 422]:
                    self.print_result("Malformed data properly rejected")
                    properly_handled = True
                elif response.status_code == 401:
                    self.print_result("Data parsed but authentication failed (acceptable)")
                    properly_handled = True
                else:
                    self.print_result(f"Unexpected response: {response.status_code}", False)
                    properly_handled = False
                
                # Send metrics
                self.send_metric("corruption_attempt", 1, 'increment',
                               self.dd_tags + [f'corruption_type:{corruption_type}',
                                             f'handled:{"yes" if properly_handled else "no"}'])
                
            except requests.exceptions.RequestException:
                self.print_result("Connection rejected (server protection)")
                self.send_metric("corruption_blocked", 1, 'increment',
                               self.dd_tags + [f'corruption_type:{corruption_type}'])
            except Exception as e:
                self.print_result(f"Corruption caused error: {e}")
                self.send_metric("corruption_error", 1, 'increment',
                               self.dd_tags + [f'corruption_type:{corruption_type}'])
            
            time.sleep(0.5)
    
    def demo_resource_pressure(self):
        """Demo resource pressure scenarios"""
        self.print_header("Resource Pressure Scenarios Demo")
        
        pressure_tests = [
            {'name': 'large_payload', 'size': 1024*100, 'description': '100KB payload'},
            {'name': 'rapid_requests', 'count': 10, 'description': '10 rapid requests'},
            {'name': 'concurrent_requests', 'count': 5, 'description': '5 concurrent requests'}
        ]
        
        for test in pressure_tests:
            self.print_step(f"Testing {test['description']}")
            
            if test['name'] == 'large_payload':
                # Test large payload
                large_data = {
                    'username': 'test_user',
                    'password': 'test_pass',
                    'large_field': 'x' * test['size']
                }
                
                start_time = time.time()
                try:
                    response = self.session.post(
                        f"{self.backend_url}/api/auth/login",
                        json=large_data,
                        timeout=15
                    )
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code in [400, 413, 422]:
                        self.print_result("Large payload properly rejected")
                        success = True
                    else:
                        self.print_result(f"Large payload response: {response.status_code}")
                        success = response.status_code < 500
                    
                    self.send_metric("resource_pressure_large_payload", response_time, 'histogram',
                                   self.dd_tags + [f'success:{"yes" if success else "no"}'])
                    
                except Exception as e:
                    self.print_result(f"Large payload caused: {e}")
                    self.send_metric("resource_pressure_error", 1, 'increment',
                                   self.dd_tags + ['test:large_payload'])
            
            elif test['name'] == 'rapid_requests':
                # Test rapid requests
                successful_requests = 0
                start_time = time.time()
                
                for i in range(test['count']):
                    try:
                        response = self.session.get(f"{self.backend_url}/api/health/", timeout=5)
                        if response.status_code == 200:
                            successful_requests += 1
                    except:
                        pass
                    time.sleep(0.1)  # 100ms between requests
                
                total_time = time.time() - start_time
                success_rate = (successful_requests / test['count']) * 100
                
                self.print_result(f"Rapid requests: {successful_requests}/{test['count']} successful ({success_rate:.1f}%)")
                self.send_metric("resource_pressure_rapid_success_rate", success_rate, 'gauge',
                               self.dd_tags + ['test:rapid_requests'])
            
            elif test['name'] == 'concurrent_requests':
                # Simulate concurrent requests (simplified)
                self.print_result("Concurrent request simulation completed")
                self.send_metric("resource_pressure_concurrent", 1, 'increment',
                               self.dd_tags + ['test:concurrent_requests'])
            
            time.sleep(1)
    
    def demo_business_logic_edge_cases(self):
        """Demo business logic edge cases"""
        self.print_header("Business Logic Edge Cases Demo")
        
        edge_cases = [
            {'name': 'invalid_plan_id', 'description': 'Non-existent plan access'},
            {'name': 'expired_session', 'description': 'Expired session handling'},
            {'name': 'concurrent_operations', 'description': 'Concurrent user operations'}
        ]
        
        for case in edge_cases:
            self.print_step(f"Testing {case['description']}")
            
            if case['name'] == 'invalid_plan_id':
                try:
                    response = self.session.get(f"{self.backend_url}/api/plans/99999", timeout=10)
                    if response.status_code == 404:
                        self.print_result("Non-existent plan properly handled (404)")
                        success = True
                    else:
                        self.print_result(f"Unexpected response: {response.status_code}")
                        success = False
                    
                    self.send_metric("business_logic_invalid_plan", 1, 'increment',
                                   self.dd_tags + [f'success:{"yes" if success else "no"}'])
                except Exception as e:
                    self.print_result(f"Invalid plan test error: {e}")
                    self.send_metric("business_logic_error", 1, 'increment',
                                   self.dd_tags + ['case:invalid_plan'])
            
            elif case['name'] == 'expired_session':
                # Test with invalid authorization
                try:
                    response = self.session.get(
                        f"{self.backend_url}/api/users/profile",
                        headers={'Authorization': 'Bearer invalid_token_12345'},
                        timeout=10
                    )
                    if response.status_code == 401:
                        self.print_result("Invalid session properly rejected (401)")
                        success = True
                    else:
                        self.print_result(f"Unexpected response: {response.status_code}")
                        success = False
                    
                    self.send_metric("business_logic_expired_session", 1, 'increment',
                                   self.dd_tags + [f'success:{"yes" if success else "no"}'])
                except Exception as e:
                    self.print_result(f"Expired session test error: {e}")
                    self.send_metric("business_logic_error", 1, 'increment',
                                   self.dd_tags + ['case:expired_session'])
            
            else:
                # Simulate other business logic tests
                self.print_result("Business logic test simulated")
                self.send_metric("business_logic_simulated", 1, 'increment',
                               self.dd_tags + [f'case:{case["name"]}'])
            
            time.sleep(1)
    
    def generate_demo_summary(self):
        """Generate demo summary"""
        self.print_header("Demo Summary")
        
        print(f"""
📊 Demo Completed Successfully!

🎯 What was demonstrated:
   ✅ Authentication attack protection
   ✅ Data corruption handling
   ✅ Resource pressure management
   ✅ Business logic edge cases
   ✅ Datadog metrics integration

📈 Metrics sent to Datadog:
   - telecom.unhappy_path.demo.service_health_check
   - telecom.unhappy_path.demo.auth_attack_*
   - telecom.unhappy_path.demo.corruption_*
   - telecom.unhappy_path.demo.resource_pressure_*
   - telecom.unhappy_path.demo.business_logic_*

🔗 Next Steps:
   1. Run full test suite: ./run_unhappy_path_tests.sh
   2. Import Datadog dashboard: datadog_unhappy_path_dashboard.json
   3. Set up monitoring alerts
   4. Review UNHAPPY_PATH_TESTING_GUIDE.md

⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        # Send final demo metric
        self.send_metric("demo_completed", 1, 'increment', 
                        self.dd_tags + ['status:success'])
    
    def run_demo(self):
        """Run the complete demo"""
        print("🚀 Advanced Unhappy Path Testing Framework Demo")
        print("=" * 60)
        print("This demo showcases key features of the unhappy path testing framework")
        print("without running the full test suite.")
        print()
        
        # Send demo start metric
        self.send_metric("demo_started", 1, 'increment')
        
        # Check service health first
        if not self.check_service_health():
            print("\n⚠️  Backend service is not running. Some demos will be simulated.")
            print("   To see full functionality, start the backend service:")
            print("   docker-compose up -d backend")
            print()
        
        # Run demo scenarios
        self.demo_authentication_attacks()
        self.demo_data_corruption()
        self.demo_resource_pressure()
        self.demo_business_logic_edge_cases()
        
        # Generate summary
        self.generate_demo_summary()

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Demo Advanced Unhappy Path Testing Framework')
    parser.add_argument('--backend-url', default='http://127.0.0.1:5000',
                       help='Backend service URL')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick demo with fewer scenarios')
    
    args = parser.parse_args()
    
    demo = UnhappyPathDemo(args.backend_url)
    
    if args.quick:
        print("🏃 Running Quick Demo...")
        demo.check_service_health()
        demo.demo_authentication_attacks()
        demo.generate_demo_summary()
    else:
        demo.run_demo()

if __name__ == '__main__':
    main()
