import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
from app.models import User
from flask_jwt_extended import decode_token
import json

class TestAuthService:
    """Unit tests for Authentication Service"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data"""
        return {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+91-9876543210'
        }
    
    def test_user_registration_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post('/api/auth/register', 
                             data=json.dumps(test_user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == test_user_data['username']
        assert data['user']['email'] == test_user_data['email']
    
    def test_user_registration_duplicate_username(self, client, test_user_data):
        """Test registration with duplicate username"""
        # Register first user
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        # Try to register with same username
        response = client.post('/api/auth/register', 
                             data=json.dumps(test_user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['error'].lower()
    
    def test_user_registration_invalid_data(self, client):
        """Test registration with invalid data"""
        invalid_data = {
            'username': '',  # Empty username
            'email': 'invalid-email',  # Invalid email
            'password': '123'  # Too short password
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_user_login_success(self, client, test_user_data):
        """Test successful user login"""
        # Register user first
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        # Login
        login_data = {
            'username': test_user_data['username'],
            'password': test_user_data['password']
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
    
    def test_user_login_invalid_credentials(self, client, test_user_data):
        """Test login with invalid credentials"""
        # Register user first
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        # Login with wrong password
        login_data = {
            'username': test_user_data['username'],
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'invalid' in data['error'].lower()
    
    def test_user_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        login_data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', 
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_token_refresh_success(self, client, test_user_data):
        """Test successful token refresh"""
        # Register and login user
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps({
                                       'username': test_user_data['username'],
                                       'password': test_user_data['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        refresh_token = login_data['refresh_token']
        
        # Refresh token
        response = client.post('/api/auth/refresh',
                             headers={'Authorization': f'Bearer {refresh_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data
    
    def test_token_refresh_invalid_token(self, client):
        """Test token refresh with invalid token"""
        response = client.post('/api/auth/refresh',
                             headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 422
    
    def test_logout_success(self, client, test_user_data):
        """Test successful logout"""
        # Register and login user
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps({
                                       'username': test_user_data['username'],
                                       'password': test_user_data['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']
        
        # Logout
        response = client.post('/api/auth/logout',
                             headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get('/api/users/profile')
        
        assert response.status_code == 401
    
    def test_protected_route_with_valid_token(self, client, test_user_data):
        """Test accessing protected route with valid token"""
        # Register and login user
        client.post('/api/auth/register', 
                   data=json.dumps(test_user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login', 
                                   data=json.dumps({
                                       'username': test_user_data['username'],
                                       'password': test_user_data['password']
                                   }),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']
        
        # Access protected route
        response = client.get('/api/users/profile',
                            headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
    
    def test_password_hashing(self, app):
        """Test password hashing functionality"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password='plaintext_password',
                first_name='Test',
                last_name='User',
                phone='+91-9876543210'
            )
            
            # Password should be hashed
            assert user.password_hash != 'plaintext_password'
            
            # Should be able to verify correct password
            assert user.check_password('plaintext_password') is True
            
            # Should reject incorrect password
            assert user.check_password('wrong_password') is False
    
    def test_user_model_validation(self, app):
        """Test user model validation"""
        with app.app_context():
            # Test valid user creation
            user = User(
                username='validuser',
                email='valid@example.com',
                password='validpass123',
                first_name='Valid',
                last_name='User',
                phone='+91-9876543210'
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            created_user = User.query.filter_by(username='validuser').first()
            assert created_user is not None
            assert created_user.email == 'valid@example.com'
    
    def test_auth_service_availability(self, client):
        """Test authentication service availability"""
        # Test if auth endpoints are accessible
        endpoints = [
            '/api/auth/register',
            '/api/auth/login',
            '/api/auth/refresh',
            '/api/auth/logout'
        ]
        
        for endpoint in endpoints:
            response = client.options(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
