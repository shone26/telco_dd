#!/usr/bin/env python3
"""
Master Test Runner Script
Orchestrates all test types: unit, integration, service availability, E2E, and error injection
"""
import sys
import os
import subprocess
import time
import json
from datetime import datetime
import argparse

class MasterTestRunner:
    """Master test runner for all test types"""
    
    def __init__(self, backend_url='http://127.0.0.1:5000', frontend_url='http://127.0.0.1:3002'):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = {}
        self.overall_start_time = None
        
    def run_command(self, command, description, timeout=300):
        """Run a command and capture results"""
        print(f"\n{'='*60}")
        print(f"🚀 {description}")
        print(f"{'='*60}")
        print(f"Command: {' '.join(command)}")
        print()
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(__file__)
            )
            
            duration = time.time() - start_time
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            
            self.test_results[description] = {
                'success': success,
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if success:
                print(f"\n✅ {description} completed successfully in {duration:.2f}s")
            else:
                print(f"\n❌ {description} failed in {duration:.2f}s (exit code: {result.returncode})")
            
            return success
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"\n⏰ {description} timed out after {duration:.2f}s")
            self.test_results[description] = {
                'success': False,
                'duration': duration,
                'return_code': -1,
                'error': 'timeout'
            }
            return False
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"\n💥 {description} failed with exception: {str(e)}")
            self.test_results[description] = {
                'success': False,
                'duration': duration,
                'return_code': -1,
                'error': str(e)
            }
            return False
    
    def run_unit_tests(self):
        """Run unit tests using pytest"""
        return self.run_command(
            ['python', '-m', 'pytest', 'unit/', '-v', '--tb=short'],
            "Unit Tests",
            timeout=180
        )
    
    def run_integration_tests(self):
        """Run integration tests using pytest"""
        return self.run_command(
            ['python', '-m', 'pytest', 'integration/', '-v', '--tb=short'],
            "Integration Tests",
            timeout=300
        )
    
    def run_service_availability_tests(self):
        """Run service availability tests"""
        return self.run_command(
            ['python', 'test_service_availability.py', 
             '--backend-url', self.backend_url,
             '--frontend-url', self.frontend_url],
            "Service Availability Tests",
            timeout=120
        )
    
    def run_e2e_happy_path_tests(self):
        """Run end-to-end happy path tests"""
        return self.run_command(
            ['python', 'test_e2e_happy_path.py',
             '--backend-url', self.backend_url,
             '--frontend-url', self.frontend_url],
            "End-to-End Happy Path Tests",
            timeout=300
        )
    
    def run_error_injection_tests(self):
        """Run error injection and unhappy path tests"""
        return self.run_command(
            ['python', 'test_error_injection.py',
             '--backend-url', self.backend_url,
             '--frontend-url', self.frontend_url],
            "Error Injection and Unhappy Path Tests",
            timeout=600
        )
    
    def wait_for_services(self, timeout=60):
        """Wait for services to be available"""
        print(f"⏳ Waiting for services to be available (timeout: {timeout}s)...")
        
        import requests
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check backend
                backend_response = requests.get(f'{self.backend_url}/api/health/', timeout=5)
                if backend_response.status_code == 200:
                    print("✅ Backend service is available")
                    
                    # Check frontend
                    try:
                        frontend_response = requests.get(self.frontend_url, timeout=5)
                        if frontend_response.status_code in [200, 302]:
                            print("✅ Frontend service is available")
                            return True
                    except:
                        pass
                    
            except:
                pass
            
            print("⏳ Services not ready yet, waiting...")
            time.sleep(5)
        
        print("❌ Timeout waiting for services")
        return False
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report"""
        total_duration = time.time() - self.overall_start_time if self.overall_start_time else 0
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': total_duration,
            'test_suites': {},
            'overall_stats': {
                'total_suites': len(self.test_results),
                'passed_suites': 0,
                'failed_suites': 0,
                'success_rate': 0
            }
        }
        
        # Process test results
        for test_name, result in self.test_results.items():
            summary['test_suites'][test_name] = {
                'success': result['success'],
                'duration': result['duration'],
                'return_code': result.get('return_code', -1)
            }
            
            if result['success']:
                summary['overall_stats']['passed_suites'] += 1
            else:
                summary['overall_stats']['failed_suites'] += 1
        
        # Calculate success rate
        if summary['overall_stats']['total_suites'] > 0:
            summary['overall_stats']['success_rate'] = (
                summary['overall_stats']['passed_suites'] / 
                summary['overall_stats']['total_suites'] * 100
            )
        
        return summary
    
    def print_final_summary(self):
        """Print final test summary"""
        summary = self.generate_summary_report()
        
        print("\n" + "="*80)
        print("🏁 FINAL TEST SUMMARY")
        print("="*80)
        
        print(f"📊 Overall Statistics:")
        print(f"   Total Test Suites: {summary['overall_stats']['total_suites']}")
        print(f"   Passed: {summary['overall_stats']['passed_suites']} ✅")
        print(f"   Failed: {summary['overall_stats']['failed_suites']} ❌")
        print(f"   Success Rate: {summary['overall_stats']['success_rate']:.1f}%")
        print(f"   Total Duration: {summary['total_duration']:.2f}s")
        
        print(f"\n📋 Test Suite Results:")
        for test_name, result in summary['test_suites'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"   {test_name}: {status} ({result['duration']:.2f}s)")
        
        # Save detailed report
        report_filename = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        return summary['overall_stats']['success_rate'] == 100.0
    
    def run_all_tests(self, test_types=None, wait_for_services=True):
        """Run all specified test types"""
        self.overall_start_time = time.time()
        
        print("🧪 TELECOM APPLICATION - COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Wait for services if requested
        if wait_for_services:
            if not self.wait_for_services():
                print("❌ Services are not available. Aborting tests.")
                return False
        
        # Define test execution order and functions
        available_tests = {
            'availability': ('Service Availability Tests', self.run_service_availability_tests),
            'unit': ('Unit Tests', self.run_unit_tests),
            'integration': ('Integration Tests', self.run_integration_tests),
            'e2e': ('End-to-End Happy Path Tests', self.run_e2e_happy_path_tests),
            'error': ('Error Injection Tests', self.run_error_injection_tests)
        }
        
        # Determine which tests to run
        if test_types is None:
            tests_to_run = available_tests
        else:
            tests_to_run = {k: v for k, v in available_tests.items() if k in test_types}
        
        print(f"\n🎯 Running {len(tests_to_run)} test suite(s):")
        for test_key, (test_name, _) in tests_to_run.items():
            print(f"   - {test_name}")
        
        # Run tests in order
        all_passed = True
        for test_key, (test_name, test_func) in tests_to_run.items():
            success = test_func()
            if not success:
                all_passed = False
                
                # Ask user if they want to continue on failure
                if len(tests_to_run) > 1:
                    try:
                        continue_choice = input(f"\n⚠️  {test_name} failed. Continue with remaining tests? (y/N): ").strip().lower()
                        if continue_choice not in ['y', 'yes']:
                            print("🛑 Test execution stopped by user.")
                            break
                    except KeyboardInterrupt:
                        print("\n🛑 Test execution interrupted by user.")
                        break
        
        # Generate and print final summary
        final_success = self.print_final_summary()
        
        return final_success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run comprehensive test suite for telecom application')
    
    parser.add_argument('--backend-url', default='http://127.0.0.1:5000',
                       help='Backend service URL')
    parser.add_argument('--frontend-url', default='http://127.0.0.1:3002',
                       help='Frontend service URL')
    parser.add_argument('--tests', nargs='+', 
                       choices=['availability', 'unit', 'integration', 'e2e', 'error'],
                       help='Specific test types to run (default: all)')
    parser.add_argument('--no-wait', action='store_true',
                       help='Do not wait for services to be available')
    parser.add_argument('--quick', action='store_true',
                       help='Run only essential tests (availability, unit, e2e)')
    
    args = parser.parse_args()
    
    # Determine test types
    if args.quick:
        test_types = ['availability', 'unit', 'e2e']
    elif args.tests:
        test_types = args.tests
    else:
        test_types = None  # Run all tests
    
    # Create and run test runner
    runner = MasterTestRunner(args.backend_url, args.frontend_url)
    
    try:
        success = runner.run_all_tests(
            test_types=test_types,
            wait_for_services=not args.no_wait
        )
        
        if success:
            print("\n🎉 ALL TESTS PASSED! The telecom application is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️  SOME TESTS FAILED. Please check the detailed reports.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
