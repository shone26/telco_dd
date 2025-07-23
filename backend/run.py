#!/usr/bin/env python3
"""
Telecom Application - Flask Backend Server
Main entry point for the Flask application
"""

import os
from app import create_app

# Initialize Datadog monitoring before importing the app
try:
    from datadog_config import configure_datadog
    configure_datadog()
    print("Datadog monitoring initialized successfully")
except ImportError:
    print("Warning: Datadog monitoring not available - ddtrace package not installed")
except Exception as e:
    print(f"Warning: Failed to initialize Datadog monitoring: {e}")

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Telecom API Server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
