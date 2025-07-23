# TeleConnect Frontend (Node.js)

A Node.js Express frontend for the TeleConnect telecom application.

## Features

- **Server-Side Rendering**: Uses EJS templates for dynamic content
- **Session Management**: Secure session-based authentication
- **API Integration**: Seamless integration with Flask backend
- **Responsive Design**: Mobile-friendly UI
- **Plan Management**: Browse, select, and manage telecom plans
- **User Dashboard**: Real-time account information and statistics
- **Profile Management**: View and manage user profile and plan history

## Technology Stack

- **Node.js** - Runtime environment
- **Express.js** - Web framework
- **EJS** - Template engine
- **Axios** - HTTP client for API calls
- **Express Session** - Session management
- **CSS3** - Styling and responsive design

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and visit:
   ```
   http://localhost:3002
   ```

## Project Structure

```
frontend/
├── server.js              # Main Express server
├── package.json           # Dependencies and scripts
├── views/                 # EJS templates
│   ├── login.ejs         # Login page
│   ├── dashboard.ejs     # User dashboard
│   ├── plans.ejs         # Plans catalog
│   ├── profile.ejs       # User profile
│   └── error.ejs         # Error page
├── public/               # Static assets
│   └── css/
│       └── styles.css    # Main stylesheet
└── README.md            # This file
```

## API Integration

The frontend communicates with the Flask backend API running on `http://127.0.0.1:5000/api`. Key endpoints:

- `POST /auth/login` - User authentication
- `GET /users/dashboard` - Dashboard data
- `GET /plans` - Available plans
- `POST /plans/subscribe` - Plan subscription
- `GET /users/profile` - User profile data

## Features Overview

### Authentication
- Session-based authentication with secure cookies
- Automatic redirection for protected routes
- Demo account quick-login functionality

### Dashboard
- Real-time account statistics
- Current plan information
- Recent activity timeline
- Quick action buttons

### Plans Management
- Browse all available plans
- Filter by category (Prepaid, Postpaid, Data Only, Popular)
- Detailed plan information modal
- One-click plan subscription

### Profile Management
- View personal information
- Plan history and status
- Payment history
- Plan management (cancel, toggle auto-renewal)

## Environment Variables

- `PORT` - Server port (default: 3002)
- `API_BASE_URL` - Backend API URL (default: http://127.0.0.1:5000/api)

## Development

For development with auto-restart:

```bash
npm install -g nodemon
npm run dev
```

## Demo Accounts

The application includes demo accounts for testing:

- **john.doe** / password123 (Has active plan)
- **jane.smith** / password456 (New user)
- **test.user** / test123 (Expiring plan)

## Backend Dependency

This frontend requires the Flask backend to be running on port 5000. Make sure to start the backend server before using the frontend:

```bash
cd ../backend
python run.py
```

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Security Features

- CSRF protection via Express sessions
- Secure cookie configuration
- Input validation and sanitization
- Authentication middleware for protected routes
