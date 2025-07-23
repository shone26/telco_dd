from app import db
from app.models import User, Plan, UserPlan, Transaction
from datetime import datetime, timedelta
import json
import os

class DataService:
    """Service to handle data initialization and management"""
    
    def __init__(self):
        self.sample_users = [
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
        
        self.sample_plans = [
            {
                'name': 'Basic Mobile Plan',
                'category': 'mobile',
                'price': 299,
                'features': [
                    '2GB Daily Data',
                    'Unlimited Calls',
                    '100 SMS/day',
                    '28 Days Validity'
                ],
                'description': 'Perfect for light users with essential connectivity needs',
                'is_popular': False
            },
            {
                'name': 'Premium Mobile Plan',
                'category': 'mobile',
                'price': 599,
                'features': [
                    '4GB Daily Data',
                    'Unlimited Calls',
                    '100 SMS/day',
                    'Netflix Mobile Subscription',
                    '28 Days Validity'
                ],
                'description': 'Best value plan with entertainment benefits',
                'is_popular': True
            },
            {
                'name': 'Unlimited Mobile Plan',
                'category': 'mobile',
                'price': 999,
                'features': [
                    'Unlimited Data',
                    'Unlimited Calls',
                    '100 SMS/day',
                    'Netflix + Amazon Prime',
                    'Disney+ Hotstar',
                    '28 Days Validity'
                ],
                'description': 'Ultimate plan for heavy data users',
                'is_popular': False
            },
            {
                'name': 'Fiber Basic Internet',
                'category': 'internet',
                'price': 799,
                'features': [
                    '100 Mbps Speed',
                    'Unlimited Data',
                    'Free Installation',
                    '24/7 Support'
                ],
                'description': 'High-speed fiber internet for home use',
                'is_popular': False
            },
            {
                'name': 'Fiber Premium Internet',
                'category': 'internet',
                'price': 1299,
                'features': [
                    '200 Mbps Speed',
                    'Unlimited Data',
                    'Free Installation',
                    'Netflix Subscription',
                    '24/7 Priority Support'
                ],
                'description': 'Premium fiber internet with entertainment benefits',
                'is_popular': True
            },
            {
                'name': 'Basic TV Package',
                'category': 'tv',
                'price': 399,
                'features': [
                    '150+ Channels',
                    'HD Quality',
                    'Free Set-top Box',
                    'Recording Feature'
                ],
                'description': 'Essential TV package for family entertainment',
                'is_popular': False
            },
            {
                'name': 'Family Bundle',
                'category': 'bundle',
                'price': 1899,
                'features': [
                    '200 Mbps Fiber Internet',
                    'Premium TV Package (300+ Channels)',
                    '2 Mobile Connections (4GB each)',
                    'Netflix + Amazon Prime',
                    'Free Installation & Setup'
                ],
                'description': 'Complete family package with internet, TV, and mobile',
                'is_popular': True
            },
            {
                'name': 'Business Bundle',
                'category': 'bundle',
                'price': 2999,
                'features': [
                    '500 Mbps Dedicated Internet',
                    '5 Mobile Connections',
                    'Business TV Package',
                    'Static IP Address',
                    'Priority Support',
                    'Free Installation'
                ],
                'description': 'Comprehensive solution for small businesses',
                'is_popular': False
            }
        ]
    
    def initialize_sample_data(self):
        """Initialize database with sample data if empty"""
        try:
            # Check if data already exists
            if User.query.first() is not None:
                print("Sample data already exists, skipping initialization")
                return
            
            print("Initializing sample data...")
            
            # Create sample users
            created_users = []
            for user_data in self.sample_users:
                user = User(**user_data)
                db.session.add(user)
                created_users.append(user)
            
            # Create sample plans
            created_plans = []
            for plan_data in self.sample_plans:
                plan = Plan(**plan_data)
                db.session.add(plan)
                created_plans.append(plan)
            
            # Commit users and plans first
            db.session.commit()
            
            # Create sample user plans and transactions
            self._create_sample_user_plans(created_users, created_plans)
            
            db.session.commit()
            print("Sample data initialized successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing sample data: {str(e)}")
            raise
    
    def _create_sample_user_plans(self, users, plans):
        """Create sample user plans and transactions"""
        # John Doe has Premium Mobile Plan (active)
        john = users[0]
        premium_mobile = next(p for p in plans if p.name == 'Premium Mobile Plan')
        
        activation_date = datetime.utcnow() - timedelta(days=15)
        renewal_date = activation_date + timedelta(days=28)
        
        john_plan = UserPlan(
            user_id=john.id,
            plan_id=premium_mobile.id,
            activation_date=activation_date,
            renewal_date=renewal_date,
            auto_renewal=True
        )
        db.session.add(john_plan)
        
        # Create transaction for John's plan
        john_transaction = Transaction(
            user_id=john.id,
            plan_id=premium_mobile.id,
            amount=premium_mobile.price,
            payment_method='credit_card'
        )
        john_transaction.mark_completed()
        db.session.add(john_transaction)
        
        # Test User has Fiber Basic Internet (expiring soon)
        test_user = users[2]
        fiber_basic = next(p for p in plans if p.name == 'Fiber Basic Internet')
        
        activation_date = datetime.utcnow() - timedelta(days=25)
        renewal_date = datetime.utcnow() + timedelta(days=3)  # Expiring in 3 days
        
        test_plan = UserPlan(
            user_id=test_user.id,
            plan_id=fiber_basic.id,
            activation_date=activation_date,
            renewal_date=renewal_date,
            auto_renewal=False
        )
        db.session.add(test_plan)
        
        # Create transaction for Test User's plan
        test_transaction = Transaction(
            user_id=test_user.id,
            plan_id=fiber_basic.id,
            amount=fiber_basic.price,
            payment_method='debit_card'
        )
        test_transaction.mark_completed()
        db.session.add(test_transaction)
        
        # Jane Smith has no current plan (new user)
        # No plan or transaction for Jane
    
    def load_data_from_json(self, json_file_path):
        """Load data from JSON file (for migration from old format)"""
        try:
            if not os.path.exists(json_file_path):
                print(f"JSON file not found: {json_file_path}")
                return False
            
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            
            if 'users' in data:
                self._import_users_from_json(data['users'])
            
            if 'plans' in data:
                self._import_plans_from_json(data['plans'])
            
            db.session.commit()
            print(f"Data imported successfully from {json_file_path}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error loading data from JSON: {str(e)}")
            return False
    
    def _import_users_from_json(self, users_data):
        """Import users from JSON data"""
        for user_data in users_data:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                continue
            
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],  # In real app, this should be hashed
                first_name=user_data['firstName'],
                last_name=user_data['lastName'],
                phone=user_data['phone']
            )
            db.session.add(user)
            
            # Import current plan if exists
            if user_data.get('currentPlan'):
                current_plan_data = user_data['currentPlan']
                plan = Plan.query.filter_by(name=current_plan_data['planId']).first()
                
                if plan:
                    activation_date = datetime.fromisoformat(current_plan_data['activationDate'])
                    renewal_date = datetime.fromisoformat(current_plan_data['renewalDate'])
                    
                    user_plan = UserPlan(
                        user_id=user.id,
                        plan_id=plan.id,
                        activation_date=activation_date,
                        renewal_date=renewal_date,
                        auto_renewal=current_plan_data.get('autoRenewal', True)
                    )
                    user_plan.status = current_plan_data.get('status', 'active')
                    db.session.add(user_plan)
            
            # Import payment history
            if user_data.get('paymentHistory'):
                for payment_data in user_data['paymentHistory']:
                    plan = Plan.query.filter_by(name=payment_data['planId']).first()
                    if plan:
                        transaction = Transaction(
                            user_id=user.id,
                            plan_id=plan.id,
                            amount=payment_data['amount'],
                            payment_method=payment_data['paymentMethod'].lower().replace(' ', '_')
                        )
                        transaction.status = payment_data['status']
                        transaction.created_at = datetime.fromisoformat(payment_data['date'])
                        db.session.add(transaction)
    
    def _import_plans_from_json(self, plans_data):
        """Import plans from JSON data"""
        for plan_data in plans_data:
            # Check if plan already exists
            existing_plan = Plan.query.filter_by(name=plan_data['name']).first()
            if existing_plan:
                continue
            
            plan = Plan(
                name=plan_data['name'],
                category=plan_data['category'],
                price=plan_data['price'],
                features=plan_data['features'],
                description=plan_data['description'],
                currency=plan_data.get('currency', 'INR'),
                duration=plan_data.get('duration', 'monthly'),
                is_popular=plan_data.get('popular', False),
                is_available=plan_data.get('available', True)
            )
            db.session.add(plan)
    
    def reset_database(self):
        """Reset database (for testing purposes)"""
        try:
            db.drop_all()
            db.create_all()
            self.initialize_sample_data()
            print("Database reset successfully")
            return True
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
            return False
    
    def get_database_stats(self):
        """Get database statistics"""
        return {
            'users_count': User.query.count(),
            'plans_count': Plan.query.count(),
            'active_plans_count': UserPlan.query.filter_by(status='active').count(),
            'transactions_count': Transaction.query.count(),
            'completed_transactions_count': Transaction.query.filter_by(status='completed').count(),
            'total_revenue': db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.status == 'completed'
            ).scalar() or 0
        }
