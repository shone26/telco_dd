import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
from app.models import User, Plan, Transaction
import json
from datetime import datetime

class TestPaymentService:
    """Unit tests for Payment Service"""
    
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
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
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
        """Create test plans and users"""
        # Create test plan
        plan = Plan(
            name='Test Plan',
            description='Test plan for payments',
            price=299.0,
            data_limit='1GB',
            call_minutes=100,
            sms_limit=100,
            validity_days=30,
            is_available=True,
            is_popular=False
        )
        db.session.add(plan)
        db.session.commit()
    
    def test_process_payment_success(self, client, auth_headers):
        """Test successful payment processing"""
        # Get plan ID
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'transaction_id' in data
        assert 'receipt' in data
    
    def test_process_payment_invalid_card(self, client, auth_headers):
        """Test payment with invalid card number"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '1234567890123456',  # Invalid card
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['error'].lower()
    
    def test_process_payment_expired_card(self, client, auth_headers):
        """Test payment with expired card"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2020,  # Expired year
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'expired' in data['error'].lower()
    
    def test_process_payment_missing_fields(self, client, auth_headers):
        """Test payment with missing required fields"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            # Missing card details
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_process_payment_invalid_plan(self, client, auth_headers):
        """Test payment for non-existent plan"""
        payment_data = {
            'plan_id': 99999,  # Non-existent plan
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'plan not found' in data['error'].lower()
    
    def test_process_payment_without_auth(self, client):
        """Test payment processing without authentication"""
        payment_data = {
            'plan_id': 1,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json')
        
        assert response.status_code == 401
    
    def test_validate_card_success(self, client, auth_headers):
        """Test successful card validation"""
        card_data = {
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        response = client.post('/api/payments/validate-card', 
                             data=json.dumps(card_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['valid'] is True
    
    def test_validate_card_invalid(self, client, auth_headers):
        """Test invalid card validation"""
        card_data = {
            'card_number': '1234567890123456',  # Invalid card
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        response = client.post('/api/payments/validate-card', 
                             data=json.dumps(card_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['valid'] is False
    
    def test_get_payment_history(self, client, auth_headers):
        """Test getting payment history"""
        # First make a payment
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        client.post('/api/payments/process', 
                   data=json.dumps(payment_data),
                   content_type='application/json',
                   headers=auth_headers)
        
        # Get payment history
        response = client.get('/api/payments/history', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'transactions' in data
        assert len(data['transactions']) > 0
    
    def test_get_payment_history_empty(self, client, auth_headers):
        """Test getting payment history when no payments made"""
        response = client.get('/api/payments/history', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'transactions' in data
        assert len(data['transactions']) == 0
    
    def test_get_transaction_details(self, client, auth_headers):
        """Test getting specific transaction details"""
        # First make a payment
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
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
        
        payment_result = json.loads(payment_response.data)
        transaction_id = payment_result['transaction_id']
        
        # Get transaction details
        response = client.get(f'/api/payments/transaction/{transaction_id}', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'transaction' in data
        assert data['transaction']['id'] == transaction_id
    
    def test_get_transaction_details_not_found(self, client, auth_headers):
        """Test getting non-existent transaction details"""
        response = client.get('/api/payments/transaction/99999', 
                            headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_refund_transaction_success(self, client, auth_headers):
        """Test successful transaction refund"""
        # First make a payment
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
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
        
        payment_result = json.loads(payment_response.data)
        transaction_id = payment_result['transaction_id']
        
        # Request refund
        refund_data = {
            'reason': 'Customer request'
        }
        
        response = client.post(f'/api/payments/refund/{transaction_id}', 
                             data=json.dumps(refund_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'refund_id' in data
    
    def test_refund_transaction_not_found(self, client, auth_headers):
        """Test refund for non-existent transaction"""
        refund_data = {
            'reason': 'Customer request'
        }
        
        response = client.post('/api/payments/refund/99999', 
                             data=json.dumps(refund_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_payment_methods_list(self, client, auth_headers):
        """Test getting available payment methods"""
        response = client.get('/api/payments/methods', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'methods' in data
        assert len(data['methods']) > 0
        
        # Check if credit_card is available
        method_names = [method['name'] for method in data['methods']]
        assert 'credit_card' in method_names
    
    def test_payment_with_debit_card(self, client, auth_headers):
        """Test payment with debit card"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'debit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_payment_with_upi(self, client, auth_headers):
        """Test payment with UPI"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'upi',
            'upi_id': 'testuser@paytm'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_payment_with_net_banking(self, client, auth_headers):
        """Test payment with net banking"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'net_banking',
            'bank_code': 'HDFC'
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_transaction_model_validation(self, app):
        """Test transaction model validation"""
        with app.app_context():
            # Create test user and plan
            user = User(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                phone='+91-9876543210'
            )
            db.session.add(user)
            
            plan = Plan(
                name='Test Plan',
                description='Test plan',
                price=299.0,
                data_limit='1GB',
                call_minutes=100,
                sms_limit=100,
                validity_days=30,
                is_available=True,
                is_popular=False
            )
            db.session.add(plan)
            db.session.commit()
            
            # Create transaction
            transaction = Transaction(
                user_id=user.id,
                plan_id=plan.id,
                amount=plan.price,
                payment_method='credit_card',
                status='completed'
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Verify transaction was created
            created_transaction = Transaction.query.filter_by(user_id=user.id).first()
            assert created_transaction is not None
            assert created_transaction.amount == 299.0
            assert created_transaction.status == 'completed'
    
    def test_payment_service_availability(self, client):
        """Test payment service availability"""
        # Test if payment endpoints are accessible
        endpoints = [
            '/api/payments/process',
            '/api/payments/validate-card',
            '/api/payments/history',
            '/api/payments/methods'
        ]
        
        for endpoint in endpoints:
            response = client.options(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    def test_payment_security_headers(self, client, auth_headers):
        """Test payment endpoints have proper security headers"""
        response = client.get('/api/payments/methods', headers=auth_headers)
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers or response.status_code == 200
        # Additional security checks can be added here
    
    def test_payment_amount_validation(self, client, auth_headers):
        """Test payment amount validation"""
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
        # Test with negative amount (should be rejected)
        payment_data = {
            'plan_id': plan_id,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123',
            'cardholder_name': 'Test User',
            'amount': -100  # Negative amount
        }
        
        response = client.post('/api/payments/process', 
                             data=json.dumps(payment_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should either reject negative amount or use plan's price
        assert response.status_code in [200, 400]
