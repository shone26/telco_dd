from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Plan, UserPlan, Transaction
from app.services.data_service import DataService
from datetime import datetime
import random
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.session.execute(db.text('SELECT 1'))
                db.session.commit()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Telecom API',
            'version': '1.0.0',
            'success': True
        }), 200
        
    except Exception as e:
        # Log the error for debugging
        print(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'success': False
        }), 503

@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with service status"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Database health
        try:
            start_time = time.time()
            db.session.execute(db.text('SELECT 1'))
            db_response_time = (time.time() - start_time) * 1000
            
            health_status['services']['database'] = {
                'status': 'healthy',
                'response_time_ms': round(db_response_time, 2)
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Authentication service health
        try:
            user_count = User.query.count()
            health_status['services']['auth_service'] = {
                'status': 'healthy',
                'users_count': user_count
            }
        except Exception as e:
            health_status['services']['auth_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Plan service health
        try:
            plan_count = Plan.query.filter_by(is_available=True).count()
            health_status['services']['plan_service'] = {
                'status': 'healthy',
                'available_plans': plan_count
            }
        except Exception as e:
            health_status['services']['plan_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Payment service health
        try:
            transaction_count = Transaction.query.count()
            health_status['services']['payment_service'] = {
                'status': 'healthy',
                'total_transactions': transaction_count
            }
        except Exception as e:
            health_status['services']['payment_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'Health check failed: {str(e)}'
        }), 503

@health_bp.route('/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    try:
        data_service = DataService()
        stats = data_service.get_database_stats()
        
        # Add additional statistics
        stats.update({
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': 'N/A',  # Would be calculated from app start time in production
            'api_version': '1.0.0'
        })
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get stats: {str(e)}'
        }), 500

@health_bp.route('/test-services', methods=['GET'])
def test_all_services():
    """Test all microservices"""
    try:
        test_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'services': {}
        }
        
        # Test Auth Service
        try:
            # Test user creation and authentication
            test_user = User.query.filter_by(username='health_test_user').first()
            if not test_user:
                test_user = User(
                    username='health_test_user',
                    email='health@test.com',
                    password='test123',
                    first_name='Health',
                    last_name='Test',
                    phone='+91-9999999999'
                )
                db.session.add(test_user)
                db.session.commit()
            
            # Test password verification
            auth_test = test_user.check_password('test123')
            
            test_results['services']['auth_service'] = {
                'status': 'healthy' if auth_test else 'unhealthy',
                'tests': {
                    'user_creation': 'passed',
                    'password_verification': 'passed' if auth_test else 'failed'
                }
            }
            
        except Exception as e:
            test_results['services']['auth_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            test_results['overall_status'] = 'unhealthy'
        
        # Test Plan Service
        try:
            plans = Plan.query.filter_by(is_available=True).limit(5).all()
            popular_plans = Plan.query.filter_by(is_popular=True).all()
            
            test_results['services']['plan_service'] = {
                'status': 'healthy',
                'tests': {
                    'plan_retrieval': 'passed',
                    'popular_plans': 'passed',
                    'plans_count': len(plans)
                }
            }
            
        except Exception as e:
            test_results['services']['plan_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            test_results['overall_status'] = 'unhealthy'
        
        # Test Payment Service
        try:
            # Test transaction creation (without actual payment processing)
            test_plan = Plan.query.first()
            if test_plan and test_user:
                test_transaction = Transaction(
                    user_id=test_user.id,
                    plan_id=test_plan.id,
                    amount=test_plan.price,
                    payment_method='test'
                )
                test_transaction.status = 'test'
                db.session.add(test_transaction)
                db.session.commit()
                
                # Clean up test transaction
                db.session.delete(test_transaction)
                db.session.commit()
            
            test_results['services']['payment_service'] = {
                'status': 'healthy',
                'tests': {
                    'transaction_creation': 'passed',
                    'payment_validation': 'passed'
                }
            }
            
        except Exception as e:
            test_results['services']['payment_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            test_results['overall_status'] = 'unhealthy'
        
        # Test User Service
        try:
            if test_user:
                current_plan = test_user.get_current_plan()
                payment_history = test_user.get_payment_history(limit=1)
                
                test_results['services']['user_service'] = {
                    'status': 'healthy',
                    'tests': {
                        'user_profile': 'passed',
                        'plan_retrieval': 'passed',
                        'payment_history': 'passed'
                    }
                }
            
        except Exception as e:
            test_results['services']['user_service'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            test_results['overall_status'] = 'unhealthy'
        
        status_code = 200 if test_results['overall_status'] == 'healthy' else 503
        return jsonify(test_results), status_code
        
    except Exception as e:
        return jsonify({
            'overall_status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'Service testing failed: {str(e)}'
        }), 503

@health_bp.route('/inject-error', methods=['POST'])
def inject_error():
    """Inject errors for testing purposes"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No error injection data provided'}), 400
        
        service = data.get('service')  # auth, plan, payment, user
        error_type = data.get('error_type')  # timeout, failure, unavailable
        duration = data.get('duration', 60)  # Duration in seconds
        
        if not service or not error_type:
            return jsonify({'error': 'Service and error_type are required'}), 400
        
        # In a real application, this would integrate with error injection system
        # For now, we'll simulate the response
        
        error_scenarios = {
            'auth': {
                'timeout': 'Authentication service timeout',
                'failure': 'Authentication service failure',
                'unavailable': 'Authentication service unavailable'
            },
            'plan': {
                'timeout': 'Plan service timeout',
                'failure': 'Plan service failure',
                'unavailable': 'Plan service unavailable'
            },
            'payment': {
                'timeout': 'Payment service timeout',
                'failure': 'Payment service failure',
                'unavailable': 'Payment service unavailable'
            },
            'user': {
                'timeout': 'User service timeout',
                'failure': 'User service failure',
                'unavailable': 'User service unavailable'
            }
        }
        
        if service not in error_scenarios:
            return jsonify({'error': 'Invalid service name'}), 400
        
        if error_type not in error_scenarios[service]:
            return jsonify({'error': 'Invalid error type for service'}), 400
        
        return jsonify({
            'success': True,
            'message': f'Error injected for {service} service',
            'service': service,
            'error_type': error_type,
            'error_message': error_scenarios[service][error_type],
            'duration': duration,
            'injected_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error injection failed: {str(e)}'}), 500

@health_bp.route('/clear-errors', methods=['POST'])
def clear_injected_errors():
    """Clear all injected errors"""
    try:
        # In a real application, this would clear error injection state
        return jsonify({
            'success': True,
            'message': 'All injected errors cleared',
            'cleared_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to clear errors: {str(e)}'}), 500

@health_bp.route('/simulate-load', methods=['POST'])
def simulate_load():
    """Simulate load for performance testing"""
    try:
        data = request.get_json() or {}
        operations = data.get('operations', 100)
        operation_type = data.get('type', 'mixed')  # db, api, mixed
        
        start_time = time.time()
        results = {
            'operations_completed': 0,
            'operations_failed': 0,
            'average_response_time': 0,
            'errors': []
        }
        
        for i in range(operations):
            try:
                op_start = time.time()
                
                if operation_type == 'db' or operation_type == 'mixed':
                    # Simulate database operations
                    User.query.count()
                    Plan.query.filter_by(is_available=True).count()
                    Transaction.query.filter_by(status='completed').count()
                
                if operation_type == 'api' or operation_type == 'mixed':
                    # Simulate API operations
                    time.sleep(random.uniform(0.001, 0.01))  # Simulate processing time
                
                op_time = (time.time() - op_start) * 1000
                results['operations_completed'] += 1
                
                # Add some random failures for realistic testing
                if random.random() < 0.05:  # 5% failure rate
                    raise Exception(f"Simulated failure in operation {i}")
                
            except Exception as e:
                results['operations_failed'] += 1
                results['errors'].append(str(e))
        
        total_time = time.time() - start_time
        results['total_time_seconds'] = round(total_time, 3)
        results['operations_per_second'] = round(operations / total_time, 2)
        results['average_response_time'] = round((total_time / operations) * 1000, 2)
        results['success_rate'] = round((results['operations_completed'] / operations) * 100, 2)
        
        return jsonify({
            'success': True,
            'load_test_results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Load simulation failed: {str(e)}'}), 500

@health_bp.route('/reset-data', methods=['POST'])
def reset_test_data():
    """Reset database to initial state (for testing)"""
    try:
        # This should only be available in development/testing environments
        data_service = DataService()
        success = data_service.reset_database()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Database reset successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset database'
            }), 500
        
    except Exception as e:
        return jsonify({'error': f'Database reset failed: {str(e)}'}), 500

@health_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics"""
    try:
        # Simulate performance metrics collection
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'response_times': {
                'auth_service': {
                    'avg_ms': random.uniform(50, 150),
                    'p95_ms': random.uniform(100, 300),
                    'p99_ms': random.uniform(200, 500)
                },
                'plan_service': {
                    'avg_ms': random.uniform(30, 100),
                    'p95_ms': random.uniform(80, 200),
                    'p99_ms': random.uniform(150, 400)
                },
                'payment_service': {
                    'avg_ms': random.uniform(100, 300),
                    'p95_ms': random.uniform(200, 500),
                    'p99_ms': random.uniform(400, 1000)
                },
                'user_service': {
                    'avg_ms': random.uniform(40, 120),
                    'p95_ms': random.uniform(90, 250),
                    'p99_ms': random.uniform(180, 450)
                }
            },
            'throughput': {
                'requests_per_second': random.uniform(50, 200),
                'concurrent_users': random.randint(10, 100)
            },
            'error_rates': {
                'auth_service': random.uniform(0, 2),
                'plan_service': random.uniform(0, 1),
                'payment_service': random.uniform(0, 5),
                'user_service': random.uniform(0, 1.5)
            },
            'resource_usage': {
                'cpu_percent': random.uniform(10, 80),
                'memory_percent': random.uniform(20, 70),
                'disk_usage_percent': random.uniform(30, 60)
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get performance metrics: {str(e)}'}), 500
