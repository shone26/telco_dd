-- Database initialization script for Telecom Application
-- This script sets up the initial database schema and data

-- Create database if it doesn't exist (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS telecom_db;

-- Use the database
-- \c telecom_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create plans table
CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    duration VARCHAR(20) DEFAULT 'monthly',
    features TEXT NOT NULL,
    description TEXT,
    is_popular BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_plans table (for user subscriptions)
CREATE TABLE IF NOT EXISTS user_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES plans(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active',
    activation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    renewal_date TIMESTAMP,
    auto_renewal BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES plans(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    transaction_reference VARCHAR(100),
    failure_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_plans_user_id ON user_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_user_plans_status ON user_plans(status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- Insert sample plans
INSERT INTO plans (name, category, price, features, description, is_popular, is_available) VALUES
('Basic Plan', 'mobile', 199.00, '["1GB Daily Data", "100 Minutes", "100 SMS", "30 Days Validity"]', 'Perfect for light users with essential features', FALSE, TRUE),
('Standard Plan', 'mobile', 399.00, '["3GB Daily Data", "300 Minutes", "300 SMS", "30 Days Validity"]', 'Great for regular users with balanced features', FALSE, TRUE),
('Premium Plan', 'mobile', 599.00, '["5GB Daily Data", "500 Minutes", "500 SMS", "Netflix Mobile", "30 Days Validity"]', 'Ideal for heavy users with premium features', TRUE, TRUE),
('Unlimited Plan', 'mobile', 999.00, '["Unlimited Data", "Unlimited Calls", "Unlimited SMS", "Netflix + Amazon Prime", "30 Days Validity"]', 'Ultimate plan with unlimited everything', TRUE, TRUE),
('Student Plan', 'mobile', 149.00, '["2GB Daily Data", "150 Minutes", "200 SMS", "30 Days Validity"]', 'Special discounted plan for students', FALSE, TRUE),
('Family Plan', 'bundle', 1299.00, '["10GB Shared Data", "1000 Minutes", "1000 SMS", "Multiple Connections", "30 Days Validity"]', 'Shared plan for families with multiple connections', TRUE, TRUE),
('Business Plan', 'bundle', 799.00, '["8GB Daily Data", "800 Minutes", "800 SMS", "Business Support", "30 Days Validity"]', 'Professional plan for business users', FALSE, TRUE),
('Weekend Plan', 'mobile', 299.00, '["2GB Daily Data", "200 Minutes", "250 SMS", "Weekend Benefits", "30 Days Validity"]', 'Special plan with weekend benefits', FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- Insert sample admin user (password: admin123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone) VALUES
('admin', 'admin@telecom.com', 'pbkdf2:sha256:600000$rtFZpBeHQqw72dmq$c85a0bcf462a1381cee1f7bfc70f7ef40cb2643ae6587b5d28b659d907c00471', 'Admin', 'User', '+91-9999999999')
ON CONFLICT DO NOTHING;

-- Insert sample regular user (password: user123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone) VALUES
('testuser', 'test@example.com', 'pbkdf2:sha256:600000$BeLAEMvt18gXxfs7$257af403cfa20fe1329268f7c1af68886e319f7890df081c1df4a21b6ca3c4c2', 'Test', 'User', '+91-9876543210')
ON CONFLICT DO NOTHING;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plans_updated_at BEFORE UPDATE ON plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_plans_updated_at BEFORE UPDATE ON user_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO telecom_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO telecom_user;

-- Create views for common queries
CREATE OR REPLACE VIEW active_user_plans AS
SELECT 
    up.id,
    up.user_id,
    up.plan_id,
    u.username,
    u.email,
    p.name as plan_name,
    p.price,
    p.category,
    p.features,
    up.activation_date,
    up.renewal_date,
    up.auto_renewal,
    up.status
FROM user_plans up
JOIN users u ON up.user_id = u.id
JOIN plans p ON up.plan_id = p.id
WHERE up.status = 'active';

CREATE OR REPLACE VIEW user_transaction_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(t.id) as total_transactions,
    SUM(CASE WHEN t.status = 'completed' THEN t.amount ELSE 0 END) as total_spent,
    MAX(t.created_at) as last_transaction_date
FROM users u
LEFT JOIN transactions t ON u.id = t.user_id
GROUP BY u.id, u.username, u.email;

-- Insert some sample transactions for demo
INSERT INTO transactions (user_id, plan_id, amount, payment_method, status, transaction_reference) VALUES
(2, 1, 199.00, 'credit_card', 'completed', 'TXN_001_' || EXTRACT(EPOCH FROM NOW())::TEXT),
(2, 3, 599.00, 'debit_card', 'completed', 'TXN_002_' || EXTRACT(EPOCH FROM NOW())::TEXT)
ON CONFLICT DO NOTHING;

-- Insert sample user plan subscription
INSERT INTO user_plans (user_id, plan_id, status, activation_date, renewal_date) VALUES
(2, 3, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 days')
ON CONFLICT DO NOTHING;

COMMIT;
