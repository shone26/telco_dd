import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
from app.models import User, Plan, UserPlan
import json

class TestPlanService:
    """Unit tests for Plan Service"""
    
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
        """Create test plans"""
        plans = [
            Plan(
                name='Basic Plan',
                description='Basic telecom plan',
                price=299.0,
                data_limit='1GB',
                call_minutes=100,
                sms_limit=100,
                validity_days=30,
                is_available=True,
                is_popular=False
            ),
            Plan(
                name='Premium Plan',
                description='Premium telecom plan',
                price=599.0,
                data_limit='5GB',
                call_minutes=500,
                sms_limit=500,
                validity_days=30,
                is_available=True,
                is_popular=True
            ),
            Plan(
                name='Unlimited Plan',
                description='Unlimited telecom plan',
                price=999.0,
                data_limit='Unlimited',
                call_minutes=999999,
                sms_limit=999999,
                validity_days=30,
                is_available=True,
                is_popular=True
            ),
            Plan(
                name='Discontinued Plan',
                description='Old plan no longer available',
                price=199.0,
                data_limit='500MB',
                call_minutes=50,
                sms_limit=50,
                validity_days=30,
                is_available=False,
                is_popular=False
            )
        ]
        
        for plan in plans:
            db.session.add(plan)
        db.session.commit()
    
    def test_get_all_plans_success(self, client, auth_headers):
        """Test getting all available plans"""
        response = client.get('/api/plans', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plans' in data
        assert len(data['plans']) == 3  # Only available plans
        
        # Check that discontinued plan is not included
        plan_names = [plan['name'] for plan in data['plans']]
        assert 'Discontinued Plan' not in plan_names
    
    def test_get_all_plans_without_auth(self, client):
        """Test getting plans without authentication"""
        response = client.get('/api/plans')
        
        assert response.status_code == 401
    
    def test_get_popular_plans_success(self, client, auth_headers):
        """Test getting popular plans"""
        response = client.get('/api/plans/popular', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plans' in data
        assert len(data['plans']) == 2  # Premium and Unlimited plans
        
        # Verify all returned plans are popular
        for plan in data['plans']:
            assert plan['is_popular'] is True
    
    def test_get_plan_by_id_success(self, client, auth_headers):
        """Test getting a specific plan by ID"""
        # First get all plans to get a valid ID
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        response = client.get(f'/api/plans/{plan_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plan' in data
        assert data['plan']['id'] == plan_id
    
    def test_get_plan_by_id_not_found(self, client, auth_headers):
        """Test getting a non-existent plan"""
        response = client.get('/api/plans/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_get_plan_by_id_unavailable(self, client, auth_headers):
        """Test getting an unavailable plan"""
        # Get the discontinued plan ID
        with client.application.app_context():
            discontinued_plan = Plan.query.filter_by(name='Discontinued Plan').first()
            plan_id = discontinued_plan.id
        
        response = client.get(f'/api/plans/{plan_id}', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_subscribe_to_plan_success(self, client, auth_headers):
        """Test successful plan subscription"""
        # Get a plan ID
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
        
        response = client.post('/api/plans/subscribe', 
                             data=json.dumps(subscription_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'subscription' in data
    
    def test_subscribe_to_invalid_plan(self, client, auth_headers):
        """Test subscription to invalid plan"""
        subscription_data = {
            'plan_id': 99999,
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': 12,
            'expiry_year': 2025,
            'cvv': '123'
        }
        
        response = client.post('/api/plans/subscribe', 
                             data=json.dumps(subscription_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_subscribe_without_payment_info(self, client, auth_headers):
        """Test subscription without payment information"""
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        subscription_data = {
            'plan_id': plan_id
            # Missing payment information
        }
        
        response = client.post('/api/plans/subscribe', 
                             data=json.dumps(subscription_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_user_current_plan(self, client, auth_headers):
        """Test getting user's current plan"""
        # First subscribe to a plan
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
        
        # Now get current plan
        response = client.get('/api/plans/current', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'plan' in data
        assert data['plan']['id'] == plan_id
    
    def test_get_user_current_plan_no_subscription(self, client, auth_headers):
        """Test getting current plan when user has no active subscription"""
        response = client.get('/api/plans/current', headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'no active plan' in data['error'].lower()
    
    def test_cancel_plan_success(self, client, auth_headers):
        """Test successful plan cancellation"""
        # First subscribe to a plan
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
        
        # Cancel the plan
        response = client.post(f'/api/plans/cancel/{plan_id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_cancel_plan_not_subscribed(self, client, auth_headers):
        """Test cancelling a plan user is not subscribed to"""
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        plan_id = plans_data['plans'][0]['id']
        
        response = client.post(f'/api/plans/cancel/{plan_id}', 
                             headers=auth_headers)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_toggle_auto_renewal_success(self, client, auth_headers):
        """Test toggling auto-renewal"""
        # First subscribe to a plan
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
        
        # Toggle auto-renewal
        response = client.post(f'/api/plans/toggle-auto-renewal/{plan_id}', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_plan_model_validation(self, app):
        """Test plan model validation"""
        with app.app_context():
            # Test valid plan creation
            plan = Plan(
                name='Test Plan',
                description='Test plan description',
                price=399.0,
                data_limit='2GB',
                call_minutes=200,
                sms_limit=200,
                validity_days=30,
                is_available=True,
                is_popular=False
            )
            
            db.session.add(plan)
            db.session.commit()
            
            # Verify plan was created
            created_plan = Plan.query.filter_by(name='Test Plan').first()
            assert created_plan is not None
            assert created_plan.price == 399.0
            assert created_plan.is_available is True
    
    def test_plan_service_availability(self, client):
        """Test plan service availability"""
        # Test if plan endpoints are accessible
        endpoints = [
            '/api/plans',
            '/api/plans/popular',
            '/api/plans/current',
            '/api/plans/subscribe'
        ]
        
        for endpoint in endpoints:
            response = client.options(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    def test_plan_filtering_by_price(self, client, auth_headers):
        """Test plan filtering functionality"""
        response = client.get('/api/plans?max_price=500', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # All returned plans should be under 500
        for plan in data['plans']:
            assert plan['price'] <= 500
    
    def test_plan_search_functionality(self, client, auth_headers):
        """Test plan search functionality"""
        response = client.get('/api/plans?search=premium', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Should return plans matching search term
        if data['plans']:
            found_premium = any('premium' in plan['name'].lower() or 
                              'premium' in plan['description'].lower() 
                              for plan in data['plans'])
            assert found_premium
    
    def test_plan_comparison_feature(self, client, auth_headers):
        """Test plan comparison functionality"""
        # Get multiple plan IDs
        plans_response = client.get('/api/plans', headers=auth_headers)
        plans_data = json.loads(plans_response.data)
        
        if len(plans_data['plans']) >= 2:
            plan_ids = [plans_data['plans'][0]['id'], plans_data['plans'][1]['id']]
            
            response = client.post('/api/plans/compare', 
                                 data=json.dumps({'plan_ids': plan_ids}),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'comparison' in data
