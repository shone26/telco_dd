from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    current_plans = db.relationship('UserPlan', back_populates='user', lazy='dynamic')
    payment_history = db.relationship('Transaction', back_populates='user', lazy='dynamic')
    
    def __init__(self, username, email, password, first_name, last_name, phone):
        # Explicitly don't set ID - let database auto-increment handle it
        # Don't call super().__init__() to avoid any parent class ID generation
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        # Explicitly set other fields to avoid any defaults
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_active = True
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convert user object to dictionary"""
        user_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
        
        if include_sensitive:
            user_dict['password_hash'] = self.password_hash
            
        return user_dict
    
    def get_current_plan(self):
        """Get user's current active plan"""
        current_plan = self.current_plans.filter_by(
            status='active'
        ).order_by(UserPlan.activation_date.desc()).first()
        
        return current_plan
    
    def get_payment_history(self, limit=10):
        """Get user's payment history"""
        return self.payment_history.order_by(
            Transaction.created_at.desc()
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserPlan(db.Model):
    __tablename__ = 'user_plans'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    activation_date = db.Column(db.DateTime, nullable=False)
    renewal_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, expired, cancelled
    auto_renewal = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='current_plans')
    plan = db.relationship('Plan', back_populates='user_plans')
    
    def __init__(self, user_id, plan_id, activation_date, renewal_date, auto_renewal=True):
        self.user_id = user_id
        self.plan_id = plan_id
        self.activation_date = activation_date
        self.renewal_date = renewal_date
        self.auto_renewal = auto_renewal
    
    def to_dict(self):
        """Convert user plan object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'activation_date': self.activation_date.isoformat() if self.activation_date else None,
            'renewal_date': self.renewal_date.isoformat() if self.renewal_date else None,
            'status': self.status,
            'auto_renewal': self.auto_renewal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'plan': self.plan.to_dict() if self.plan else None
        }
    
    def is_expiring_soon(self, days=7):
        """Check if plan is expiring within specified days"""
        if self.status != 'active':
            return False
        
        days_until_renewal = (self.renewal_date - datetime.utcnow()).days
        return days_until_renewal <= days
    
    def is_expired(self):
        """Check if plan has expired"""
        return self.renewal_date < datetime.utcnow()
    
    def get_status(self):
        """Get current status of the plan"""
        if self.is_expired():
            return 'expired'
        elif self.is_expiring_soon():
            return 'expiring_soon'
        else:
            return 'active'
    
    def __repr__(self):
        return f'<UserPlan {self.user_id}:{self.plan_id}>'
