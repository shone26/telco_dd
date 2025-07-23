# Telecom Web Application

A comprehensive telecom service management web application built with Python Flask backend and vanilla JavaScript frontend. This application allows users to manage their telecom services, view plans, make payments, and track their usage.

## 🚀 Features

### User Features
- **User Authentication**: Secure login/logout with JWT tokens
- **Dashboard**: Overview of current plans, payments, and notifications
- **Plan Management**: Browse, compare, and subscribe to telecom plans
- **Payment Processing**: Secure payment gateway simulation
- **Profile Management**: Update personal information and preferences
- **Notifications**: Real-time alerts for plan renewals and payments

### Admin Features
- **Service Health Monitoring**: Real-time health checks for all microservices
- **Error Injection**: Testing capabilities for fault tolerance
- **Performance Metrics**: System performance monitoring
- **Load Testing**: Simulate high traffic scenarios

### Technical Features
- **Microservices Architecture**: Modular backend services
- **RESTful API**: Well-documented API endpoints
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Error Handling**: Robust error management and recovery
- **Responsive Design**: Mobile-first responsive UI

## 🏗️ Architecture

The application follows a microservices architecture with the following components:

### Backend (Python Flask)
- **Authentication Service**: User login, registration, and JWT management
- **Plan Service**: Telecom plan catalog and subscription management
- **Payment Service**: Payment processing and transaction management
- **User Service**: User profile and preference management
- **Health Service**: System monitoring and testing utilities

### Frontend (HTML/CSS/JavaScript)
- **Login Page**: User authentication interface
- **Dashboard**: Main user portal
- **Plans Page**: Plan browsing and comparison
- **Payment Page**: Payment processing interface
- **Confirmation Page**: Transaction confirmations

### Database (SQLite/PostgreSQL)
- **Users**: User accounts and authentication
- **Plans**: Available telecom plans
- **UserPlans**: User subscriptions and renewals
- **Transactions**: Payment history and records

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd telecom_application
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Variables (Optional)
Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=sqlite:///telecom_app.db
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

### 3. Frontend Setup
No additional setup required for the frontend. The application uses vanilla JavaScript and can be served directly from the file system or a simple HTTP server.

## 🚀 Running the Application

### 1. Start the Backend Server
```bash
cd backend
python run.py
```

The API server will start at `http://127.0.0.1:5000`

### 2. Start the Frontend
You can serve the frontend in several ways:

#### Option A: Simple HTTP Server (Python)
```bash
cd src
python -m http.server 3000
```
Access at `http://localhost:3000`

#### Option B: Node.js HTTP Server
```bash
cd src
npx http-server -p 3000
```

#### Option C: Open directly in browser
Open `src/index.html` directly in your web browser.

## 👤 Demo Accounts

The application comes with pre-configured demo accounts:

| Username | Password | Description |
|----------|----------|-------------|
| john.doe | password123 | User with active premium mobile plan |
| jane.smith | password456 | New user without any plans |
| test.user | test123 | User with expiring fiber internet plan |

## 🧪 Testing

### Backend API Testing

#### Health Check
```bash
curl http://127.0.0.1:5000/api/health/
```

#### Detailed Health Check
```bash
curl http://127.0.0.1:5000/api/health/detailed
```

#### Test All Services
```bash
curl http://127.0.0.1:5000/api/health/test-services
```

### Error Injection Testing
```bash
# Inject authentication service error
curl -X POST http://127.0.0.1:5000/api/health/inject-error \
  -H "Content-Type: application/json" \
  -d '{"service": "auth", "error_type": "timeout", "duration": 60}'

# Clear all injected errors
curl -X POST http://127.0.0.1:5000/api/health/clear-errors
```

### Load Testing
```bash
# Simulate 100 operations
curl -X POST http://127.0.0.1:5000/api/health/simulate-load \
  -H "Content-Type: application/json" \
  -d '{"operations": 100, "type": "mixed"}'
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password

### Plan Endpoints
- `GET /api/plans/` - Get all plans
- `GET /api/plans/{id}` - Get specific plan
- `GET /api/plans/categories` - Get plan categories
- `POST /api/plans/subscribe` - Subscribe to plan
- `GET /api/plans/my-plans` - Get user's plans

### Payment Endpoints
- `POST /api/payments/process` - Process payment
- `GET /api/payments/history` - Get payment history
- `GET /api/payments/methods` - Get payment methods
- `POST /api/payments/validate-card` - Validate card details

### User Endpoints
- `GET /api/users/dashboard` - Get dashboard data
- `GET /api/users/notifications` - Get notifications
- `GET /api/users/activity` - Get user activity
- `GET /api/users/stats` - Get user statistics

### Health Endpoints
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed` - Detailed health status
- `GET /api/health/stats` - System statistics
- `POST /api/health/inject-error` - Inject errors for testing

## 🔧 Configuration

### Backend Configuration
The backend can be configured using environment variables:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Database connection string
- `FLASK_ENV`: Environment (development/production)
- `FLASK_DEBUG`: Debug mode (True/False)
- `FLASK_HOST`: Server host (default: 127.0.0.1)
- `FLASK_PORT`: Server port (default: 5000)

### Frontend Configuration
Update the `API_BASE_URL` in the frontend JavaScript files to match your backend server URL.

## 🧪 Testing Features

### Service Availability Testing
- Health checks for all microservices
- Database connectivity testing
- Response time monitoring

### Happy Path Testing
- Complete user registration and login flow
- Plan subscription and payment process
- Plan renewal and cancellation

### Error Injection Testing
- Simulate service failures
- Test error handling and recovery
- Validate user experience during failures

### Unhappy Path Testing
- Invalid login attempts
- Payment failures
- Network timeouts
- Data validation errors

## 📱 Mobile Responsiveness

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Various screen sizes and orientations

## 🔒 Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- Input validation and sanitization
- XSS prevention
- CORS configuration
- Secure session management

## 🚀 Deployment

### Production Deployment
For production deployment, consider:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set up a reverse proxy (Nginx, Apache)
3. Use a production database (PostgreSQL, MySQL)
4. Configure SSL/TLS certificates
5. Set up monitoring and logging
6. Configure environment variables securely

### Docker Deployment (Optional)
```dockerfile
# Example Dockerfile for backend
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation
- Review the test cases
- Use the health check endpoints for debugging
- Check the browser console for frontend issues

## 🔄 Version History

- **v1.0.0** - Initial release with core features
  - User authentication and management
  - Plan browsing and subscription
  - Payment processing
  - Comprehensive testing suite
  - Health monitoring and error injection

## 🎯 Future Enhancements

- Real payment gateway integration
- SMS and email notifications
- Advanced analytics dashboard
- Multi-language support
- Mobile app development
- Advanced reporting features
