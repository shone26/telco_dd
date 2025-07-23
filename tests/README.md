# Telecom Application Test Suite

This directory contains comprehensive test cases for the telecom application, covering all aspects of testing from unit tests to end-to-end integration tests.

## 📁 Directory Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_auth_service.py       # Authentication service tests
│   ├── test_plan_service.py       # Plan service tests
│   ├── test_payment_service.py    # Payment service tests
│   └── test_user_service.py       # User service tests
├── integration/                    # Integration tests for service interactions
│   └── test_service_integration.py # Cross-service integration tests
├── utils/                          # Test utilities and helpers
│   └── test_helpers.py            # Common test utilities and data generators
├── test_service_availability.py   # Service availability and health tests
├── test_e2e_happy_path.py         # End-to-end happy path tests
├── test_error_injection.py        # Error injection and unhappy path tests
├── run_all_tests.py               # Master test runner
└── README.md                      # This file
```

## 🧪 Test Types

### 1. Unit Tests (`unit/`)
Tests individual components and services in isolation.

**Coverage:**
- Authentication service (registration, login, token management)
- Plan service (CRUD operations, filtering, search)
- Payment service (processing, validation, history)
- User service (profile management, preferences, dashboard)

**Run Command:**
```bash
cd tests
python -m pytest unit/ -v
```

### 2. Integration Tests (`integration/`)
Tests interactions between different services and components.

**Coverage:**
- Service-to-service communication
- Data flow across services
- Transaction consistency
- Error propagation
- Authentication integration

**Run Command:**
```bash
cd tests
python -m pytest integration/ -v
```

### 3. Service Availability Tests
Tests the availability and health of all microservices.

**Coverage:**
- Service ping tests
- Health check endpoints
- Database connectivity
- Service endpoint availability
- Performance metrics

**Run Command:**
```bash
cd tests
python test_service_availability.py
```

**Options:**
```bash
# Test specific URLs
python test_service_availability.py --backend-url http://localhost:5000 --frontend-url http://localhost:3002

# Wait for services to be available
python test_service_availability.py --wait-for-services --timeout 60
```

### 4. End-to-End Happy Path Tests
Tests complete user journeys from registration to plan subscription.

**Coverage:**
- User registration and login
- Plan browsing and selection
- Payment processing
- Subscription verification
- Dashboard access
- Payment history

**Run Command:**
```bash
cd tests
python test_e2e_happy_path.py
```

### 5. Error Injection and Unhappy Path Tests
Tests system behavior under failure conditions and with invalid inputs.

**Coverage:**
- Service failure scenarios
- Timeout handling
- Invalid input validation
- Unauthorized access attempts
- Cascade failure detection
- Service recovery testing

**Run Command:**
```bash
cd tests
python test_error_injection.py
```

**Options:**
```bash
# Test specific service and error type
python test_error_injection.py --service auth --error-type failure --duration 30

# Test all error scenarios
python test_error_injection.py --service all --error-type all
```

## 🚀 Quick Start

### Prerequisites

1. **Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Start Services:**
   ```bash
   # Terminal 1: Start Backend
   cd backend
   python run.py

   # Terminal 2: Start Frontend
   cd frontend
   npm start
   ```

### Running All Tests

Use the master test runner to execute all test types:

```bash
cd tests
python run_all_tests.py
```

**Options:**
```bash
# Run specific test types
python run_all_tests.py --tests availability unit e2e

# Quick test (essential tests only)
python run_all_tests.py --quick

# Custom service URLs
python run_all_tests.py --backend-url http://localhost:5000 --frontend-url http://localhost:3002

# Don't wait for services
python run_all_tests.py --no-wait
```

## 📊 Test Reports

All test scripts generate detailed reports:

- **Service Availability:** `service_availability_report.json`
- **E2E Happy Path:** `e2e_happy_path_report.json`
- **Error Injection:** `error_injection_report.json`
- **Master Test Runner:** `test_summary_YYYYMMDD_HHMMSS.json`

## 🛠️ Test Utilities

The `utils/test_helpers.py` file provides:

### TestDataGenerator
Generates realistic test data for users, plans, and payments.

```python
from test_helpers import TestDataGenerator

# Generate test user
user_data = TestDataGenerator.generate_user_data('test_user')

# Generate test plan
plan_data = TestDataGenerator.generate_plan_data('test_plan')

# Generate payment data
payment_data = TestDataGenerator.generate_payment_data(plan_id, 'credit_card')
```

### APITestHelper
Simplifies API testing with authentication handling.

```python
from test_helpers import APITestHelper

helper = APITestHelper(client)
auth_result = helper.create_authenticated_user()
plans = helper.get_plans(auth_result['auth_headers'])
```

### ErrorInjector
Injects errors into services for fault tolerance testing.

```python
from test_helpers import ErrorInjector

injector = ErrorInjector(client)
injector.simulate_service_timeout('payment', duration=30)
injector.clear_all_errors()
```

### PerformanceTester
Measures response times and performs load testing.

```python
from test_helpers import PerformanceTester

tester = PerformanceTester(client)
result = tester.measure_response_time('/api/plans', headers=auth_headers)
load_result = tester.load_test_endpoint('/api/plans', concurrent_requests=10)
```

## 🎯 Testing Scenarios

### Happy Path Testing
1. User registers successfully
2. User logs in with valid credentials
3. User browses available plans
4. User selects a plan and views details
5. User processes payment successfully
6. User's subscription is activated
7. User accesses dashboard with current plan
8. User views payment history

### Unhappy Path Testing
1. Invalid login credentials
2. Expired or invalid payment cards
3. Non-existent plan access attempts
4. Unauthorized API access
5. Invalid input data validation
6. Service timeout scenarios
7. Service failure handling
8. Cascade failure detection

### Error Injection Scenarios
- **Authentication Service:** Login failures, token expiration
- **Plan Service:** Timeout during plan retrieval
- **Payment Service:** Payment processing failures
- **User Service:** Profile access failures
- **Database:** Connection failures, query timeouts

## 📈 Performance Testing

### Load Testing
```bash
# Test endpoint performance
python -c "
from test_helpers import PerformanceTester
import requests
session = requests.Session()
tester = PerformanceTester(session)
result = tester.load_test_endpoint('http://localhost:5000/api/plans', 
                                  concurrent_requests=10, 
                                  total_requests=100)
print(result)
"
```

### Response Time Monitoring
All test scripts include response time measurements and report performance metrics.

## 🔧 Configuration

### Environment Variables
```bash
export BACKEND_URL=http://localhost:5000
export FRONTEND_URL=http://localhost:3002
export TEST_TIMEOUT=300
```

### Test Configuration
Modify test parameters in individual test files:
- Timeout values
- Retry attempts
- Test data generation
- Error injection duration

## 🚨 Troubleshooting

### Common Issues

1. **Services Not Available**
   ```bash
   # Check if services are running
   curl http://localhost:5000/api/health/
   curl http://localhost:3002/
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   curl http://localhost:5000/api/health/detailed
   ```

3. **Test Dependencies**
   ```bash
   # Install missing dependencies
   pip install pytest pytest-flask requests
   ```

4. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x tests/*.py
   ```

### Debug Mode
Run tests with verbose output:
```bash
python test_service_availability.py --verbose
python -m pytest unit/ -v -s
```

## 📝 Adding New Tests

### Unit Test Template
```python
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from app import create_app, db
import json

class TestNewService:
    @pytest.fixture
    def app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    def test_new_functionality(self, client):
        # Your test code here
        pass
```

### Integration Test Template
```python
def test_new_integration(self, client, auth_headers):
    # Test service interactions
    response = client.get('/api/endpoint', headers=auth_headers)
    assert response.status_code == 200
```

## 📚 Best Practices

1. **Test Isolation:** Each test should be independent
2. **Data Cleanup:** Clean up test data after each test
3. **Realistic Data:** Use realistic test data generators
4. **Error Handling:** Test both success and failure scenarios
5. **Performance:** Include performance assertions
6. **Documentation:** Document test purposes and expected outcomes

## 🤝 Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate documentation
3. Include both positive and negative test cases
4. Update this README if adding new test types
5. Ensure tests are deterministic and repeatable

## 📞 Support

For issues with the test suite:
1. Check service availability first
2. Review test logs and reports
3. Verify test data and configuration
4. Check for dependency issues
5. Consult the troubleshooting section

---

**Happy Testing! 🧪✨**
