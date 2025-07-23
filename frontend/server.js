const tracer = require('dd-trace').init({
    logInjection: true
});

// Initialize Datadog monitoring first (before other imports)
let statsClient = null;
try {
    const { configureDatadog, createStatsClient, createRequestTrackingMiddleware } = require('./datadog_config');
    const tracer = configureDatadog();
    statsClient = createStatsClient();
    console.log('Datadog monitoring initialized successfully');
} catch (error) {
    console.log('Warning: Datadog monitoring not available:', error.message);
}

const express = require('express');
const path = require('path');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3002;
const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:5001/api';

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// Add Datadog request tracking middleware
if (statsClient) {
    try {
        const { createRequestTrackingMiddleware } = require('./datadog_config');
        app.use(createRequestTrackingMiddleware(statsClient));
    } catch (error) {
        console.log('Warning: Could not add Datadog request tracking middleware:', error.message);
    }
}
app.use(session({
    secret: 'telecom-frontend-secret',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 } // 24 hours
}));

// Set EJS as template engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use('/static', express.static(path.join(__dirname, 'public')));

// Middleware to check authentication
const requireAuth = (req, res, next) => {
    if (!req.session.user || !req.session.accessToken) {
        return res.redirect('/login');
    }
    next();
};




// Routes

// Health check endpoint for frontend
app.get('/health', (req, res) => {
    try {
        res.status(200).json({
            status: 'healthy',
            service: 'telecom-frontend',
            timestamp: new Date().toISOString(),
            version: '1.0.0',
            success: true
        });
    } catch (error) {
        res.status(503).json({
            status: 'unhealthy',
            service: 'telecom-frontend',
            timestamp: new Date().toISOString(),
            error: error.message,
            success: false
        });
    }
});

// Login page
app.get('/', (req, res) => {
    if (req.session.user) {
        return res.redirect('/dashboard');
    }
    res.render('login', { error: null });
});

app.get('/login', (req, res) => {
    if (req.session.user) {
        return res.redirect('/dashboard');
    }
    res.render('login', { error: null });
});

// Login POST
app.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        const response = await axios.post(`${API_BASE_URL}/auth/login`, {
            username,
            password
        });

        if (response.data.success) {
            req.session.user = response.data.user;
            req.session.accessToken = response.data.access_token;
            req.session.refreshToken = response.data.refresh_token;
            
            res.redirect('/dashboard');
        } else {
            res.render('login', { error: response.data.error || 'Login failed' });
        }
    } catch (error) {
        console.error('Login error:', error.message);
        res.render('login', { error: 'Network error. Please try again.' });
    }
});

// Dashboard
app.get('/dashboard', requireAuth, async (req, res) => {
    try {
        // Fetch dashboard data
        const dashboardResponse = await axios.get(`${API_BASE_URL}/users/dashboard`, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        // Fetch available plans
        const plansResponse = await axios.get(`${API_BASE_URL}/plans`, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.render('dashboard', {
            user: req.session.user,
            dashboard: dashboardResponse.data.dashboard,
            plans: plansResponse.data.plans.slice(0, 3) // Show only first 3 plans
        });
    } catch (error) {
        console.error('Dashboard error:', error.message);
        res.render('dashboard', {
            user: req.session.user,
            dashboard: null,
            plans: [],
            error: 'Failed to load dashboard data'
        });
    }
});

// Plans page
app.get('/plans', requireAuth, async (req, res) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/plans`, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.render('plans', {
            user: req.session.user,
            plans: response.data.plans,
            selectedPlan: req.query.selected || null
        });
    } catch (error) {
        console.error('Plans error:', error.message);
        res.render('plans', {
            user: req.session.user,
            plans: [],
            selectedPlan: null,
            error: 'Failed to load plans'
        });
    }
});

// Checkout page
app.get('/checkout/:planId', requireAuth, async (req, res) => {
    try {
        const planId = req.params.planId;
        
        // Get plan details
        const response = await axios.get(`${API_BASE_URL}/plans/${planId}`, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        if (response.data.success) {
            res.render('checkout', {
                user: req.session.user,
                plan: response.data.plan
            });
        } else {
            res.render('checkout', {
                user: req.session.user,
                plan: null,
                error: 'Plan not found'
            });
        }
    } catch (error) {
        console.error('Checkout error:', error.message);
        res.render('checkout', {
            user: req.session.user,
            plan: null,
            error: 'Failed to load plan details'
        });
    }
});

// Process payment
app.post('/process-payment', requireAuth, async (req, res) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/payments/process`, req.body, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.json(response.data);
    } catch (error) {
        console.error('Payment processing error:', error.message);
        if (error.response && error.response.data) {
            res.json(error.response.data);
        } else {
            res.json({ success: false, error: 'Payment processing failed' });
        }
    }
});

// Plan subscription (simplified - redirects to checkout)
app.post('/subscribe', requireAuth, async (req, res) => {
    try {
        const { plan_id } = req.body;
        res.json({ success: true, redirect: `/checkout/${plan_id}` });
    } catch (error) {
        console.error('Subscription error:', error.message);
        res.json({ success: false, error: 'Network error during subscription' });
    }
});

// Profile page
app.get('/profile', requireAuth, async (req, res) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/users/profile`, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.render('profile', {
            user: req.session.user,
            profile: response.data.user
        });
    } catch (error) {
        console.error('Profile error:', error.message);
        res.render('profile', {
            user: req.session.user,
            profile: req.session.user,
            error: 'Failed to load profile data'
        });
    }
});

// Plan management endpoints
app.post('/plans/cancel/:planId', requireAuth, async (req, res) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/plans/cancel/${req.params.planId}`, {}, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.json(response.data);
    } catch (error) {
        console.error('Cancel plan error:', error.message);
        res.json({ success: false, error: 'Failed to cancel plan' });
    }
});

app.post('/plans/toggle-auto-renewal/:planId', requireAuth, async (req, res) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/plans/toggle-auto-renewal/${req.params.planId}`, {}, {
            headers: { 'Authorization': `Bearer ${req.session.accessToken}` }
        });

        res.json(response.data);
    } catch (error) {
        console.error('Toggle auto-renewal error:', error.message);
        res.json({ success: false, error: 'Failed to toggle auto-renewal' });
    }
});

// Logout
app.post('/logout', (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            console.error('Logout error:', err);
        }
        res.redirect('/login');
    });
});

app.get('/logout', (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            console.error('Logout error:', err);
        }
        res.redirect('/login');
    });
});

// Enhanced error handling middleware
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    
    // Send JSON response for API requests
    if (req.path.startsWith('/api/') || req.headers.accept?.includes('application/json')) {
        return res.status(500).json({
            success: false,
            error: 'Internal Server Error',
            timestamp: new Date().toISOString()
        });
    }
    
    // Render error page for regular requests
    res.status(500).render('error', { 
        error: 'Internal Server Error',
        user: req.session?.user || null
    });
});

// Enhanced 404 handler
app.use((req, res) => {
    console.log(`404 - Page not found: ${req.method} ${req.path}`);
    
    // Send JSON response for API requests
    if (req.path.startsWith('/api/') || req.headers.accept?.includes('application/json')) {
        return res.status(404).json({
            success: false,
            error: 'Page Not Found',
            path: req.path,
            timestamp: new Date().toISOString()
        });
    }
    
    // Render error page for regular requests
    res.status(404).render('error', { 
        error: 'Page Not Found',
        user: req.session?.user || null
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Frontend server running on http://localhost:${PORT}`);
    console.log(`Backend API: ${API_BASE_URL}`);
});
