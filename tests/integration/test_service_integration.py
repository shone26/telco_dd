import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
from app.models import User, Plan, UserPlan, Transaction
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor

class TestServiceIntegration:
    """Integration tests for service interactions"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers"""
        # Register and login a test user
        user_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'testpass123',
            'first_name': 'Integration',
            'last_name': 'Test',
            'phone': '+91-9876543210'
        }
        
        client.post('/api/auth/register', 
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps({
                                       'username': user_data['username'],
                                       'password': user_data['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        return {'Authorization': f'Bearer {login_data["access_token"]}'}
    
    def _create_test_data(self):
        """Create test plans"""
        plans = [
            Plan(
                name='Basic Integration Plan',
                description='Basic plan for integration testing',
                price=199.0,
                data_limit='1GB',
                call_minutes=100,
                sms_limit=100,
                validity_days=30,
                is_available=True,
                is_popular=False
            ),
            Plan(
                name='Premium Integration Plan',
                description='Premium plan for integration testing',
                price=499.0,
                data_limit='5GB',
                call_minutes=500,
                sms_limit=500,
                validity_days=30,
                is_available=True,
                is_popular=True
            )
        ]
        
        for plan in plans:
            db.session.add(plan)
        db.session.commit()
    
    def test_complete_user_journey_happy_path(self, client):
        """Test complete user journey from registration to plan subscription"""
        # Step 1: User Registration
        user_data = {
            'username': 'journeyuser',
            'email': 'journey@example.com',
            'password': 'testpass123',
            'first_name': 'Journey',
            'last_name': 'User',
            'phone': '+91-9876543210'
        }
        
        register_response = client.post('/api/auth/register', 
                                      data=json.dumps(user_data),
                                      content_type='application/json')
        
        assert register_response.status_code == 201
        register_data = json.loads(register_response.data)
        assert register_data['success'] is True
        
        # Step 2: User Login
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps({
                                       'username': user_data['username'],
                                       'password': user_data['password']
                                   }),
                                   content_type='application/json')
        
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        assert login_data['success'] is True
        
        auth_headers = {'Authorization': f'Bearer {login_data["access_token"]}'}
        
        # Step 3: Browse Plans
        plans_response = client.get('/api/plans', headers=auth_headers)
        
        assert plans_response.status_code == 200
        plans_data = json.loads(plans_response.data)
        assert plans_data['success'] is True
        assert len(plans_data['plans']) > 0
        
        # Step 4: Select a Plan
        selected_plan = plans_data['plans'][0]
        plan_id = selected_plan['id']
        
        plan_details_response = client.get(f'/api/plans/{plan_id}', headers=auth_headers)
        
        assert plan_details_response.status_code == 200
        plan_details_data = json.loads(plan_details_response.data)
        assert plan_details_data['success'] is True
        
        # Step 5: Process Payment and Subscribe
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Journey User'
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 200
        payment_result = json.loads(payment_response.data)
        assert payment_result['success'] is True
        
        # Step 6: Verify Subscription
        current_plan_response = client.get('/api/users/current-plan', headers=auth_headers)
        
        assert current_plan_response.status_code == 200
        current_plan_data = json.loads(current_plan_response.data)
        assert current_plan_data['success'] is True
        assert current_plan_data['plan']['id'] == plan_id
        
        # Step 7: Check Dashboard
        dashboard_response = client.get('/api/users/dashboard', headers=auth_headers)
        
        assert dashboard_response.status_code == 200
        dashboard_data = json.loads(dashboard_response.data)
        assert dashboard_data['success'] is True
        assert 'current_plan' in dashboard_data['dashboard']
        
        # Step 8: Check Payment History
        history_response = client.get('/api/users/payment-history', headers=auth_headers)
        
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        assert history_data['success'] is True
        assert len(history_data['transactions']) > 0
    
    def test_auth_plan_service_integration(self, client, auth_headers):
        """Test authentication and plan service integration"""
        # Test that authenticated user can access plans
        response = client.get('/api/plans', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Test that unauthenticated user cannot access plans
        response = client.get('/api/plans')
        
        assert response.status_code == 401
    
    def test_plan_payment_service_integration(self, client, auth_headers):
        """Test plan and payment service integration"""
        # Get available plans
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        plan_price = plans_data['plans'][0]['price']
        
        # Process payment for the plan
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 200
        payment_result = json.loads(payment_response.data)
        assert payment_result['success'] is True
        
        # Verify transaction was created with correct plan details
        transaction_id = payment_result['transaction_id']
        transaction_response = client.get(f'/api/payments/transaction/{transaction_id}', 
                                        headers=auth_headers)
        
        assert transaction_response.status_code == 200
        transaction_data = json.loads(transaction_response.data)
        assert transaction_data['transaction']['plan_id'] == plan_id
        assert transaction_data['transaction']['amount'] == plan_price
    
    def test_user_plan_service_integration(self, client, auth_headers):
        """Test user and plan service integration"""
        # Subscribe to a plan
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        subscription_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        client.post('/api/plans/subscribe', 
                   data=json.dumps(subscription_data),
                   content_type='application/json',
                   headers=auth_headers)
        
        # Verify user's current plan
        current_plan_response = client.get('/api/users/current-plan', headers=auth_headers)
        
        assert current_plan_response.status_code == 200
        current_plan_data = json.loads(current_plan_response.data)
        assert current_plan_data['plan']['id'] == plan_id
        
        # Verify plan appears in user dashboard
        dashboard_response = client.get('/api/users/dashboard', headers=auth_headers)
        dashboard_data = json.loads(dashboard_response.data)
        assert dashboard_data['dashboard']['current_plan'] is not None
    
    def test_payment_user_service_integration(self, client, auth_headers):
        """Test payment and user service integration"""
        # Make a payment
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        client.post('/api/payments/process', 
                   data=json.dumps(payment_data),
                   content_type='application/json',
                   headers=auth_headers)
        
        # Verify payment appears in user's payment history
        history_response = client.get('/api/users/payment-history', headers=auth_headers)
        
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        assert len(history_data['transactions']) > 0
        
        # Verify payment appears in general payment history
        payment_history_response = client.get('/api/payments/history', headers=auth_headers)
        
        assert payment_history_response.status_code == 200
        payment_history_data = json.loads(payment_history_response.data)
        assert len(payment_history_data['transactions']) > 0
    
    def test_service_error_propagation(self, client, auth_headers):
        """Test error propagation between services"""
        # Test payment with invalid plan ID
        payment_data = {
            'plan_id': 99999,  # Non-existent plan
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 404
        payment_result = json.loads(payment_response.data)
        assert payment_result['success'] is False
        assert 'plan not found' in payment_result['error'].lower()
    
    def test_concurrent_service_access(self, client, auth_headers):
        """Test concurrent access to services"""
        def make_request():
            response = client.get('/api/plans', headers=auth_headers)
            return response.status_code == 200
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(results)
    
    def test_service_transaction_consistency(self, client, auth_headers):
        """Test transaction consistency across services"""
        # Get initial state
        initial_plans_response = client.get('/api/plans', headers=auth_headers)
        initial_plans_data = json.loads(initial_plans_response.data)
        plan_id = initial_plans_data['plans'][0]['id']
        
        initial_history_response = client.get('/api/users/payment-history', headers=auth_headers)
        initial_history_data = json.loads(initial_history_response.data)
        initial_transaction_count = len(initial_history_data['transactions'])
        
        # Make a payment
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 200
        
        # Verify consistency across services
        # 1. Payment service should have the transaction
        final_history_response = client.get('/api/users/payment-history', headers=auth_headers)
        final_history_data = json.loads(final_history_response.data)
        assert len(final_history_data['transactions']) == initial_transaction_count + 1
        
        # 2. User service should show the current plan
        current_plan_response = client.get('/api/users/current-plan', headers=auth_headers)
        assert current_plan_response.status_code == 200
        current_plan_data = json.loads(current_plan_response.data)
        assert current_plan_data['plan']['id'] == plan_id
    
    def test_service_data_validation_integration(self, client, auth_headers):
        """Test data validation across service boundaries"""
        # Test that invalid data is rejected consistently
        invalid_payment_data = {
            'plan_id': 'invalid',  # Should be integer
            'payment_method': 'invalid_method',
            'card_number': '123',  # Too short
            'expiry_month': 13,  # Invalid month
            'expiry_year': 2020,  # Expired
            'cvv': '12345'  # Too long
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(invalid_payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 400
        payment_result = json.loads(payment_response.data)
        assert payment_result['success'] is False
    
    def test_service_authentication_integration(self, client):
        """Test authentication integration across all services"""
        # Test that all protected endpoints require authentication
        protected_endpoints = [
            ('/api/plans', 'GET'),
            ('/api/users/profile', 'GET'),
            ('/api/users/dashboard', 'GET'),
            ('/api/payments/history', 'GET'),
            ('/api/payments/process', 'POST')
        ]
        
        for endpoint, method in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, 
                                     data=json.dumps({}),
                                     content_type='application/json')
            
            assert response.status_code == 401
    
    def test_service_performance_integration(self, client, auth_headers):
        """Test performance across service integrations"""
        start_time = time.time()
        
        # Perform a series of operations
        operations = [
            lambda: client.get('/api/plans', headers=auth_headers),
            lambda: client.get('/api/users/profile', headers=auth_headers),
            lambda: client.get('/api/users/dashboard', headers=auth_headers),
            lambda: client.get('/api/payments/methods', headers=auth_headers)
        ]
        
        for operation in operations:
            response = operation()
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All operations should complete within reasonable time
        assert total_time < 5.0  # 5 seconds threshold
    
    def test_service_health_check_integration(self, client):
        """Test health check integration across services"""
        # Test basic health check
        health_response = client.get('/api/health/')
        
        assert health_response.status_code == 200
        health_data = json.loads(health_response.data)
        assert health_data['status'] == 'healthy'
        
        # Test detailed health check
        detailed_health_response = client.get('/api/health/detailed')
        
        assert detailed_health_response.status_code == 200
        detailed_health_data = json.loads(detailed_health_response.data)
        assert 'services' in detailed_health_data
        
        # All services should be healthy
        for service_name, service_status in detailed_health_data['services'].items():
            assert service_status['status'] == 'healthy'
    
    def test_service_rollback_integration(self, client, auth_headers):
        """Test rollback behavior when service operations fail"""
        # This test would verify that if a payment fails, 
        # no subscription is created and no transaction is recorded
        
        # Attempt payment with invalid card
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        invalid_payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '1234567890123456',  # Invalid card
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        payment_response = client.post('/api/payments/process', 
                                     data=json.dumps(invalid_payment_data),
                                     content_type='application/json',
                                     headers=auth_headers)
        
        assert payment_response.status_code == 400
        
        # Verify no subscription was created
        current_plan_response = client.get('/api/users/current-plan', headers=auth_headers)
        assert current_plan_response.status_code == 404
        
        # Verify no transaction was recorded
        history_response = client.get('/api/users/payment-history', headers=auth_headers)
        history_data = json.loads(history_response.data)
        
        # Should have no successful transactions
        successful_transactions = [t for t in history_data['transactions'] 
                                 if t.get('status') == 'completed']
        assert len(successful_transactions) == 0
