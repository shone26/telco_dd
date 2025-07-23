from app import db
from app.models.user import User, UserPlan
from app.models.plan import Plan, Transaction
from datetime import datetime, timedelta
import json
import os
from functools import lru_cache
import threading

class OptimizedDataService:
    """Optimized data service with caching and performance improvements"""
    
    _initialization_lock = threading.Lock()
    _initialized = False
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    @classmethod
    def initialize_sample_data_once(cls):
        """Initialize sample data only once using singleton pattern"""
        if cls._initialized:
            return
        
        with cls._initialization_lock:
            if cls._initialized:
                return
            
            try:
                # Check if data already exists
                if User.query.first() is not None:
                    print("Sample data already exists, skipping initialization")
                    cls._initialized = True
                    return
                
                print("Initializing sample data (one-time operation)...")
                
                # Use bulk insert for better performance
                cls._bulk_insert_sample_data()
                
                cls._initialized = True
                print("Sample data initialized successfully")
                
            except Exception as e:
                print(f"Error initializing sample data: {str(e)}")
                raise
    
    @classmethod
    def _bulk_insert_sample_data(cls):
        """Bulk insert sample data for better performance"""
        # Create sample users
        sample_users_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@email.com',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+91-9876543210'
            },
            {
                'username': 'jane.smith',
                'email': 'jane.smith@email.com',
                'password': 'password456',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone': '+91-9876543211'
            },
            {
                'username': 'test.user',
                'email': 'test.user@email.com',
                'password': 'test123',
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '+91-9876543212'
            }
        ]
        
        # Create sample plans
        sample_plans_data = [
            {
                'name': 'Basic Mobile Plan',
                'category': 'mobile',
                'price': 299,
                'features': ['2GB Daily Data', 'Unlimited Calls', '100 SMS/day', '28 Days Validity'],
                'description': 'Perfect for light users with essential connectivity needs',
                'is_popular': False
            },
            {
                'name': 'Premium Mobile Plan',
                'category': 'mobile',
                'price': 599,
                'features': ['4GB Daily Data', 'Unlimited Calls', '100 SMS/day', 'Netflix Mobile', '28 Days Validity'],
                'description': 'Best value plan with entertainment benefits',
                'is_popular': True
            },
            {
                'name': 'Fiber Basic Internet',
                'category': 'internet',
                'price': 799,
                'features': ['100 Mbps Speed', 'Unlimited Data', 'Free Installation', '24/7 Support'],
                'description': 'High-speed fiber internet for home use',
                'is_popular': False
            },
            {
                'name': 'Family Bundle',
                'category': 'bundle',
                'price': 1899,
                'features': ['200 Mbps Internet', '300+ TV Channels', '2 Mobile Connections', 'Netflix + Prime'],
                'description': 'Complete family package',
                'is_popular': True
            }
        ]
        
        # Create and add users
        created_users = []
        for user_data in sample_users_data:
            user = User(**user_data)
            db.session.add(user)
            created_users.append(user)
        
        # Create and add plans
        created_plans = []
        for plan_data in sample_plans_data:
            plan = Plan(**plan_data)
            db.session.add(plan)
            created_plans.append(plan)
        
        # Commit users and plans first
        db.session.commit()
        
        # Create sample user plans and transactions
        john = created_users[0]
        premium_mobile = created_plans[1]
        
        activation_date = datetime.utcnow() - timedelta(days=15)
        renewal_date = activation_date + timedelta(days=28)
        
        user_plan = UserPlan(john.id, premium_mobile.id, activation_date, renewal_date)
        db.session.add(user_plan)
        
        transaction = Transaction(john.id, premium_mobile.id, premium_mobile.price, 'credit_card')
        transaction.mark_completed()
        db.session.add(transaction)
        
        db.session.commit()
    
    @lru_cache(maxsize=128)
    def get_plans_by_category_cached(self, category):
        """Get plans by category with caching"""
        return Plan.query.filter_by(category=category, is_available=True).all()
    
    @lru_cache(maxsize=64)
    def get_popular_plans_cached(self):
        """Get popular plans with caching"""
        return Plan.query.filter_by(is_popular=True, is_available=True).all()
    
    def get_database_stats_cached(self):
        """Get database statistics with caching"""
        cache_key = 'db_stats'
        now = datetime.utcnow()
        
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (now - timestamp).seconds < self._cache_timeout:
                return cached_data
        
        # Calculate stats
        stats = {
            'users_count': User.query.count(),
            'plans_count': Plan.query.count(),
            'active_plans_count': UserPlan.query.filter_by(status='active').count(),
            'transactions_count': Transaction.query.count(),
            'completed_transactions_count': Transaction.query.filter_by(status='completed').count(),
            'total_revenue': db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.status == 'completed'
            ).scalar() or 0
        }
        
        # Cache the results
        self._cache[cache_key] = (stats, now)
        return stats
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        # Clear LRU caches
        self.get_plans_by_category_cached.cache_clear()
        self.get_popular_plans_cached.cache_clear()
