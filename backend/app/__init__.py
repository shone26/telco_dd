from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'telecom-app-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Database configuration
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'DATABASE_URL', 
            'sqlite:///telecom_app.db'
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    
    # Enable CORS for all routes
    CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002', 'http://127.0.0.1:3000', 'http://127.0.0.1:3001', 'http://127.0.0.1:3002', 'file://'])
    
    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.plan_routes import plan_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.user_routes import user_bp
    from app.routes.health_routes import health_bp
    from app.routes.optimized_plan_routes import optimized_plan_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(plan_bp, url_prefix='/api/plans')
    app.register_blueprint(optimized_plan_bp, url_prefix='/api/optimized-plans')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize with sample data
        from app.services.data_service import DataService
        data_service = DataService()
        data_service.initialize_sample_data()
    
    # Enhanced Error handlers with proper logging
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f"404 error: {error}")
        return {'error': 'Resource not found', 'success': False}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        db.session.rollback()  # Rollback any failed transactions
        return {'error': 'Internal server error', 'success': False}, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"400 error: {error}")
        return {'error': 'Bad request', 'success': False}, 400
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        db.session.rollback()
        return {'error': 'An unexpected error occurred', 'success': False}, 500
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authorization token is required'}, 401
    
    return app
