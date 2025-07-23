from app import db
from sqlalchemy import text

# Import all model classes
from .user import User, UserPlan
from .plan import Plan, Transaction

# Make models available at package level
__all__ = ['User', 'UserPlan', 'Plan', 'Transaction', 'create_performance_indexes']

# Add database indexes for performance optimization
def create_performance_indexes():
    """Create database indexes for better query performance"""
    try:
        # Plans table indexes
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_plans_category ON plans(category)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_plans_popular ON plans(is_popular)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_plans_available ON plans(is_available)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_plans_price ON plans(price)'))
        
        # User plans table indexes
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_plans_user_id ON user_plans(user_id)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_plans_plan_id ON user_plans(plan_id)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_plans_status ON user_plans(status)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_user_plans_renewal_date ON user_plans(renewal_date)'))
        
        # Transactions table indexes
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_plan_id ON transactions(plan_id)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)'))
        
        # Users table indexes
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'))
        db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)'))
        
        db.session.commit()
        print("Database performance indexes created successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating indexes: {e}")
