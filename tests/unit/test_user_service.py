import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
from app.models import User, Plan, UserPlan, Transaction
import json

class TestUserService:
    """Unit tests for User Service"""
    
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
        # Login with existing test user
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        login_result = json.loads(login_response.data)
        return {'Authorization': f'Bearer {login_result["access_token"]}'}
    
    def _create_test_data(self):
        """Create test users and plans"""
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='+91-9876543210'
        )
        db.session.add(user)
        
        # Create test plan
        plan = Plan(
            name='Test Plan',
            description='Test plan for user service',
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
    
    def test_get_user_profile_success(self, client, auth_headers):
        """Test getting user profile"""
        response = client.get('/api/users/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == 'testuser'
        assert data['user']['email'] == 'test@example.com'
        assert 'password_hash' not in data['user']  # Password should not be exposed
    
    def test_get_user_profile_without_auth(self, client):
        """Test getting profile without authentication"""
        response = client.get('/api/users/profile')
        
        assert response.status_code == 401
    
    def test_update_user_profile_success(self, client, auth_headers):
        """Test successful profile update"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+91-9999999999'
        }
        
        response = client.put('/api/users/profile', 
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['first_name'] == 'Updated'
        assert data['user']['last_name'] == 'Name'
        assert data['user']['phone'] == '+91-9999999999'
    
    def test_update_user_profile_invalid_data(self, client, auth_headers):
        """Test profile update with invalid data"""
        update_data = {
            'email': 'invalid-email',  # Invalid email format
            'phone': '123'  # Invalid phone format
        }
        
        response = client.put('/api/users/profile', 
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_update_user_profile_duplicate_email(self, client, auth_headers):
        """Test profile update with duplicate email"""
        # Create another user first
        with client.application.app_context():
            another_user = User(
                username='anotheruser',
                email='another@example.com',
                password='password123',
                first_name='Another',
                last_name='User',
                phone='+91-8888888888'
            )
            db.session.add(another_user)
            db.session.commit()
        
        # Try to update current user's email to existing email
        update_data = {
            'email': 'another@example.com'
        }
        
        response = client.put('/api/users/profile', 
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['error'].lower()
    
    def test_change_password_success(self, client, auth_headers):
        """Test successful password change"""
        password_data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = client.post('/api/users/change-password', 
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password"""
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = client.post('/api/users/change-password', 
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'current password' in data['error'].lower()
    
    def test_change_password_mismatch(self, client, auth_headers):
        """Test password change with mismatched new passwords"""
        password_data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword123'
        }
        
        response = client.post('/api/users/change-password', 
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'passwords do not match' in data['error'].lower()
    
    def test_change_password_weak_password(self, client, auth_headers):
        """Test password change with weak password"""
        password_data = {
            'current_password': 'testpass123',
            'new_password': '123',  # Too weak
            'confirm_password': '123'
        }
        
        response = client.post('/api/users/change-password', 
                             data=json.dumps(password_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_user_dashboard(self, client, auth_headers):
        """Test getting user dashboard data"""
        response = client.get('/api/users/dashboard', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'dashboard' in data
        assert 'user_info' in data['dashboard']
        assert 'current_plan' in data['dashboard']
        assert 'usage_stats' in data['dashboard']
        assert 'recent_transactions' in data['dashboard']
    
    def test_get_user_current_plan(self, client, auth_headers):
        """Test getting user's current plan"""
        # First subscribe to a plan
        with client.application.app_context():
            plan = Plan.query.first()
            plan_id = plan.id
        
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
        
        # Get current plan
        response = client.get('/api/users/current-plan', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plan' in data
        assert data['plan']['id'] == plan_id
    
    def test_get_user_current_plan_no_subscription(self, client, auth_headers):
        """Test getting current plan when user has no subscription"""
        response = client.get('/api/users/current-plan', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'no active plan' in data['error'].lower()
    
    def test_get_user_payment_history(self, client, auth_headers):
        """Test getting user's payment history"""
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
            'cvv': '123'
        }
        
        client.post('/api/payments/process', 
                   data=json.dumps(payment_data),
                   content_type='application/json',
                   headers=auth_headers)
        
        # Get payment history
        response = client.get('/api/users/payment-history', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'transactions' in data
        assert len(data['transactions']) > 0
    
    def test_get_user_usage_stats(self, client, auth_headers):
        """Test getting user's usage statistics"""
        response = client.get('/api/users/usage-stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'usage' in data
        assert 'data_used' in data['usage']
        assert 'calls_made' in data['usage']
        assert 'sms_sent' in data['usage']
    
    def test_delete_user_account(self, client, auth_headers):
        """Test user account deletion"""
        delete_data = {
            'password': 'testpass123',
            'confirmation': 'DELETE'
        }
        
        response = client.delete('/api/users/account', 
                               data=json.dumps(delete_data),
                               content_type='application/json',
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_delete_user_account_wrong_password(self, client, auth_headers):
        """Test account deletion with wrong password"""
        delete_data = {
            'password': 'wrongpassword',
            'confirmation': 'DELETE'
        }
        
        response = client.delete('/api/users/account', 
                               data=json.dumps(delete_data),
                               content_type='application/json',
                               headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_delete_user_account_wrong_confirmation(self, client, auth_headers):
        """Test account deletion with wrong confirmation"""
        delete_data = {
            'password': 'testpass123',
            'confirmation': 'WRONG'
        }
        
        response = client.delete('/api/users/account', 
                               data=json.dumps(delete_data),
                               content_type='application/json',
                               headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_user_notifications(self, client, auth_headers):
        """Test getting user notifications"""
        response = client.get('/api/users/notifications', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'notifications' in data
    
    def test_mark_notification_read(self, client, auth_headers):
        """Test marking notification as read"""
        # This assumes notifications exist or are created
        response = client.post('/api/users/notifications/1/read', 
                             headers=auth_headers)
        
        # Should either succeed or return 404 if notification doesn't exist
        assert response.status_code in [200, 404]
    
    def test_get_user_preferences(self, client, auth_headers):
        """Test getting user preferences"""
        response = client.get('/api/users/preferences', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'preferences' in data
    
    def test_update_user_preferences(self, client, auth_headers):
        """Test updating user preferences"""
        preferences_data = {
            'email_notifications': True,
            'sms_notifications': False,
            'auto_renewal': True,
            'language': 'en'
        }
        
        response = client.put('/api/users/preferences', 
                            data=json.dumps(preferences_data),
                            content_type='application/json',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_user_model_methods(self, app):
        """Test user model methods"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Test password verification
            assert user.check_password('testpass123') is True
            assert user.check_password('wrongpassword') is False
            
            # Test user representation
            assert str(user) == 'testuser'
            
            # Test user serialization
            user_dict = user.to_dict()
            assert 'username' in user_dict
            assert 'email' in user_dict
            assert 'password_hash' not in user_dict  # Should not expose password
    
    def test_user_plan_relationship(self, app):
        """Test user-plan relationship"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            plan = Plan.query.first()
            
            # Create user plan relationship
            user_plan = UserPlan(
                user_id=user.id,
                plan_id=plan.id,
                status='active'
            )
            db.session.add(user_plan)
            db.session.commit()
            
            # Test relationship
            current_plan = user.get_current_plan()
            assert current_plan is not None
            assert current_plan.id == plan.id
    
    def test_user_transaction_relationship(self, app):
        """Test user-transaction relationship"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            plan = Plan.query.first()
            
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
            
            # Test relationship
            payment_history = user.get_payment_history()
            assert len(payment_history) > 0
            assert payment_history[0].amount == plan.price
    
    def test_user_service_availability(self, client):
        """Test user service availability"""
        # Test if user endpoints are accessible
        endpoints = [
            '/api/users/profile',
            '/api/users/dashboard',
            '/api/users/current-plan',
            '/api/users/payment-history',
            '/api/users/usage-stats',
            '/api/users/notifications',
            '/api/users/preferences'
        ]
        
        for endpoint in endpoints:
            response = client.options(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    def test_user_data_privacy(self, client, auth_headers):
        """Test user data privacy and security"""
        response = client.get('/api/users/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Sensitive data should not be exposed
        assert 'password_hash' not in data['user']
        assert 'password' not in data['user']
        
        # Only necessary data should be included
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'created_at']
        for field in expected_fields:
            assert field in data['user']
    
    def test_user_input_validation(self, client, auth_headers):
        """Test user input validation"""
        # Test with malicious input
        malicious_data = {
            'first_name': '<script>alert("xss")</script>',
            'last_name': 'DROP TABLE users;',
            'phone': '"><script>alert("xss")</script>'
        }
        
        response = client.put('/api/users/profile', 
                            data=json.dumps(malicious_data),
                            content_type='application/json',
                            headers=auth_headers)
        
        # Should either sanitize input or reject it
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Check that malicious content is sanitized
            assert '<script>' not in data['user']['first_name']
            assert 'DROP TABLE' not in data['user']['last_name']
    
    def test_user_rate_limiting(self, client, auth_headers):
        """Test rate limiting on user endpoints"""
        # Make multiple rapid requests
        for i in range(10):
            response = client.get('/api/users/profile', headers=auth_headers)
            # Should not be rate limited for reasonable requests
            assert response.status_code in [200, 429]  # 429 = Too Many Requests
