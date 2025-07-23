# 🚀 Quick Start Guide - Telecom Web Application

## Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Step-by-Step Setup

### 1. Navigate to Project Directory
```bash
cd telecom_application
```

### 2. Set Up Python Backend

#### Create Virtual Environment
```bash
cd backend
python -m venv venv
```

#### Activate Virtual Environment
**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Start Backend Server
```bash
python run.py
```

You should see output like:
```
Starting Telecom API Server...
Host: 127.0.0.1
Port: 5000
Debug: True
Environment: development
 * Running on http://127.0.0.1:5000
```

**✅ Backend is now running at http://127.0.0.1:5000**

### 3. Set Up Frontend (New Terminal Window)

#### Navigate to Frontend Directory
```bash
cd telecom_application/src
```

#### Start Frontend Server
**Option A - Using Python:**
```bash
python -m http.server 3000
```

**Option B - Using Node.js (if installed):**
```bash
npx http-server -p 3000
```

**Option C - Direct Browser Access:**
Simply open `src/index.html` in your web browser

**✅ Frontend is now running at http://localhost:3000**

### 4. Access the Application

1. Open your web browser
2. Go to `http://localhost:3000` (or open `src/index.html` directly)
3. You'll see the login page

### 5. Login with Demo Accounts

Use any of these demo accounts:

| Username | Password | Description |
|----------|----------|-------------|
| **john.doe** | password123 | User with active premium mobile plan |
| **jane.smith** | password456 | New user without any plans |
| **test.user** | test123 | User with expiring fiber internet plan |

**Tip:** Click on the username in the demo accounts section to auto-fill the login form!

## 🧪 Testing the Backend

### Test Backend API (Optional)
Open a new terminal and run:
```bash
cd telecom_application/scripts
python test_backend.py
```

This will run comprehensive tests on all API endpoints.

### Manual API Testing
You can also test individual endpoints:

```bash
# Health check
curl http://127.0.0.1:5000/api/health/

# Get all plans
curl http://127.0.0.1:5000/api/plans/

# Get payment methods
curl http://127.0.0.1:5000/api/payments/methods
```

## 🎯 What You Can Do

1. **Login** - Use demo accounts to log in
2. **Dashboard** - View current plans and statistics
3. **Browse Plans** - Explore available telecom plans
4. **Subscribe** - Subscribe to new plans (simulated)
5. **Make Payments** - Process payments (simulated)
6. **Manage Profile** - Update user information

## 🔧 Troubleshooting

### Backend Issues
- **Port 5000 in use**: Change port in `backend/run.py` or kill existing process
- **Module not found**: Make sure virtual environment is activated and dependencies installed
- **Database errors**: Delete `backend/telecom_app.db` to reset database

### Frontend Issues
- **CORS errors**: Make sure backend is running on port 5000
- **API not found**: Check that `API_BASE_URL` in frontend matches backend URL
- **Port 3000 in use**: Use a different port like `python -m http.server 8000`

### Common Solutions
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Reset database
rm backend/telecom_app.db
```

## 📱 Mobile Testing
The application is responsive! Try accessing it on your mobile device using your computer's IP address:
```
http://YOUR_COMPUTER_IP:3000
```

## 🎉 You're Ready!
Your telecom application is now running successfully. Enjoy exploring all the features!

---

**Need Help?** Check the main README.md for detailed documentation and API reference.
