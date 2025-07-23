from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.plan import Plan, Transaction
from app.models.user import User, UserPlan
from app.services.optimized_data_service import OptimizedDataService
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from functools import wraps
import time

optimized_plan_bp = Blueprint('optimized_plans', __name__)
data_service = OptimizedDataService()

def measure_performance(f):
    """Decorator to measure and log performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        
        # Log performance metrics
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Route {f.__name__} took {duration:.2f}ms")
        
        # Send custom metric to Datadog
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from datadog_config import record_histogram
            record_histogram('telecom.route.duration', duration, 
                           tags=[f'route:{f.__name__}', 'service:telecom-backend'])
        except:
            pass
        
        return result
    return decorated_function

@optimized_plan_bp.route('', methods=['GET'])
@optimized_plan_bp.route('/', methods=['GET'])
@measure_performance
def get_plans_optimized():
    """Get all available plans with optimized queries"""
    try:
        # Get query parameters
        category = request.args.get('category')
        popular_only = request.args.get('popular', '').lower() == 'true'
        search_query = request.args.get('search', '').strip()
        
        # Use optimized queries with proper indexing
        if category and not search_query and not popular_only:
            # Use cached category query
            plans = data_service.get_plans_by_category_cached(category)
        elif popular_only and not search_query and not category:
            # Use cached popular plans query
            plans = data_service.get_popular_plans_cached()
        else:
            # Build optimized query for complex filters
            query = Plan.query.filter_by(is_available=True)
            
            if category:
                query = query.filter_by(category=category)
            
            if popular_only:
                query = query.filter_by(is_popular=True)
            
            if search_query:
                # Use more efficient search
                query = query.filter(
                    db.or_(
                        Plan.name.ilike(f'%{search_query}%'),
                        Plan.description.ilike(f'%{search_query}%')
                    )
                )
            
            # Optimize ordering and limit results
            plans = query.order_by(
                Plan.is_popular.desc(), 
                Plan.price.asc()
            ).limit(50).all()  # Limit to prevent large result sets
        
        # Optimize serialization
        plans_data = []
        for plan in plans:
            plan_dict = {
                'id': plan.id,
                'name': plan.name,
                'category': plan.category,
                'price': plan.price,
                'currency': plan.currency,
                'features': plan.get_features(),
                'description': plan.description,
                'is_popular': plan.is_popular
            }
            plans_data.append(plan_dict)
        
        return jsonify({
            'success': True,
            'plans': plans_data,
            'count': len(plans_data)
        }), 200
        
    except Exception as e:
        print(f"Error in get_plans_optimized: {str(e)}")
        return jsonify({'error': f'Failed to get plans: {str(e)}'}), 500

@optimized_plan_bp.route('/my-plans', methods=['GET'])
@jwt_required()
@measure_performance
def get_user_plans_optimized():
    """Get current user's plans with optimized queries"""
    try:
        current_user_id = get_jwt_identity()
        
        # Use joinedload to prevent N+1 queries
        user_plans = UserPlan.query.options(
            joinedload(UserPlan.plan)
        ).filter_by(
            user_id=current_user_id
        ).order_by(
            UserPlan.created_at.desc()
        ).limit(20).all()  # Limit results
        
        plans_data = []
        now = datetime.utcnow()
        
        for user_plan in user_plans:
            # Calculate status efficiently
            if user_plan.renewal_date < now:
                status = 'expired'
            elif (user_plan.renewal_date - now).days <= 7:
                status = 'expiring_soon'
            else:
                status = 'active'
            
            plan_data = {
                'id': user_plan.id,
                'plan_id': user_plan.plan_id,
                'plan_name': user_plan.plan.name,
                'plan_price': user_plan.plan.price,
                'activation_date': user_plan.activation_date.isoformat(),
                'renewal_date': user_plan.renewal_date.isoformat(),
                'status': status,
                'auto_renewal': user_plan.auto_renewal,
                'days_until_renewal': (user_plan.renewal_date - now).days
            }
            plans_data.append(plan_data)
        
        return jsonify({
            'success': True,
            'plans': plans_data,
            'count': len(plans_data)
        }), 200
        
    except Exception as e:
        print(f"Error in get_user_plans_optimized: {str(e)}")
        return jsonify({'error': f'Failed to get user plans: {str(e)}'}), 500

@optimized_plan_bp.route('/stats', methods=['GET'])
@measure_performance
def get_plan_stats():
    """Get plan statistics with caching"""
    try:
        stats = data_service.get_database_stats_cached()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        print(f"Error in get_plan_stats: {str(e)}")
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@optimized_plan_bp.route('/popular', methods=['GET'])
@measure_performance
def get_popular_plans_optimized():
    """Get popular plans with caching"""
    try:
        plans = data_service.get_popular_plans_cached()
        
        plans_data = []
        for plan in plans:
            plan_dict = {
                'id': plan.id,
                'name': plan.name,
                'category': plan.category,
                'price': plan.price,
                'currency': plan.currency,
                'features': plan.get_features(),
                'description': plan.description,
                'is_popular': plan.is_popular
            }
            plans_data.append(plan_dict)
        
        return jsonify({
            'success': True,
            'plans': plans_data,
            'count': len(plans_data)
        }), 200
        
    except Exception as e:
        print(f"Error in get_popular_plans_optimized: {str(e)}")
        return jsonify({'error': f'Failed to get popular plans: {str(e)}'}), 500

@optimized_plan_bp.route('/categories', methods=['GET'])
@measure_performance
def get_categories_optimized():
    """Get all plan categories with optimized query"""
    try:
        categories = db.session.query(Plan.category).filter_by(is_available=True).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        # Get count for each category efficiently
        category_data = []
        for category in category_list:
            count = Plan.query.filter_by(category=category, is_available=True).count()
            category_data.append({
                'name': category,
                'count': count,
                'display_name': category.replace('_', ' ').title()
            })
        
        return jsonify({
            'success': True,
            'categories': category_data
        }), 200
        
    except Exception as e:
        print(f"Error in get_categories_optimized: {str(e)}")
        return jsonify({'error': f'Failed to get categories: {str(e)}'}), 500
