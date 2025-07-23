from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Plan, User, UserPlan, Transaction
from datetime import datetime, timedelta

plan_bp = Blueprint('plans', __name__)

@plan_bp.route('', methods=['GET'])
@plan_bp.route('/', methods=['GET'])
def get_plans():
    """Get all available plans with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get('category')
        popular_only = request.args.get('popular', '').lower() == 'true'
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = Plan.query.filter_by(is_available=True)
        
        if category:
            query = query.filter_by(category=category)
        
        if popular_only:
            query = query.filter_by(is_popular=True)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Plan.name.contains(search_query),
                    Plan.description.contains(search_query)
                )
            )
        
        plans = query.order_by(Plan.is_popular.desc(), Plan.price.asc()).all()
        
        return jsonify({
            'success': True,
            'plans': [plan.to_dict() for plan in plans],
            'count': len(plans)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get plans: {str(e)}'}), 500

@plan_bp.route('/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get specific plan details"""
    try:
        plan = Plan.query.get(plan_id)
        
        if not plan or not plan.is_available:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Get additional statistics
        plan_data = plan.to_dict()
        plan_data['subscribers_count'] = plan.get_active_subscribers_count()
        plan_data['total_revenue'] = plan.get_total_revenue()
        
        return jsonify({
            'success': True,
            'plan': plan_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get plan: {str(e)}'}), 500

@plan_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all plan categories"""
    try:
        categories = db.session.query(Plan.category).filter_by(is_available=True).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        # Get count for each category
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
        return jsonify({'error': f'Failed to get categories: {str(e)}'}), 500

@plan_bp.route('/popular', methods=['GET'])
def get_popular_plans():
    """Get popular plans"""
    try:
        plans = Plan.query.filter_by(is_popular=True, is_available=True).order_by(Plan.price.asc()).all()
        
        return jsonify({
            'success': True,
            'plans': [plan.to_dict() for plan in plans],
            'count': len(plans)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get popular plans: {str(e)}'}), 500

@plan_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe_to_plan():
    """Subscribe user to a plan"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        plan_id = data.get('plan_id')
        payment_method = data.get('payment_method', 'credit_card')
        auto_renewal = data.get('auto_renewal', True)
        
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        # Get plan
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_available:
            return jsonify({'error': 'Plan not found or unavailable'}), 404
        
        # Check if user already has an active plan of the same category
        existing_plan = UserPlan.query.filter_by(
            user_id=current_user_id,
            status='active'
        ).join(Plan).filter(Plan.category == plan.category).first()
        
        if existing_plan:
            return jsonify({
                'error': f'You already have an active {plan.category} plan. Please cancel it first or wait for it to expire.'
            }), 409
        
        # Create transaction
        transaction = Transaction(
            user_id=current_user_id,
            plan_id=plan_id,
            amount=plan.price,
            payment_method=payment_method
        )
        
        db.session.add(transaction)
        db.session.flush()  # Get transaction ID
        
        # Simulate payment processing
        # In real application, this would integrate with payment gateway
        payment_success = True  # Simulate successful payment
        
        if payment_success:
            # Mark transaction as completed
            transaction.mark_completed()
            
            # Create user plan
            activation_date = datetime.utcnow()
            renewal_date = activation_date + timedelta(days=30)  # Default 30 days
            
            user_plan = UserPlan(
                user_id=current_user_id,
                plan_id=plan_id,
                activation_date=activation_date,
                renewal_date=renewal_date,
                auto_renewal=auto_renewal
            )
            
            db.session.add(user_plan)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plan subscription successful',
                'transaction': transaction.to_dict(),
                'user_plan': user_plan.to_dict()
            }), 201
        else:
            # Mark transaction as failed
            transaction.mark_failed('Payment processing failed')
            db.session.commit()
            
            return jsonify({
                'error': 'Payment processing failed',
                'transaction': transaction.to_dict()
            }), 402
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Subscription failed: {str(e)}'}), 500

@plan_bp.route('/my-plans', methods=['GET'])
@jwt_required()
def get_user_plans():
    """Get current user's plans"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all user plans
        user_plans = UserPlan.query.filter_by(user_id=current_user_id).order_by(
            UserPlan.created_at.desc()
        ).all()
        
        plans_data = []
        for user_plan in user_plans:
            plan_data = user_plan.to_dict()
            plan_data['status'] = user_plan.get_status()  # Get dynamic status
            plan_data['days_until_renewal'] = (user_plan.renewal_date - datetime.utcnow()).days
            plans_data.append(plan_data)
        
        return jsonify({
            'success': True,
            'plans': plans_data,
            'count': len(plans_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user plans: {str(e)}'}), 500

@plan_bp.route('/current-plan', methods=['GET'])
@jwt_required()
def get_current_plan():
    """Get user's current active plan"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_plan = user.get_current_plan()
        
        if not current_plan:
            return jsonify({
                'success': True,
                'current_plan': None,
                'message': 'No active plan found'
            }), 200
        
        plan_data = current_plan.to_dict()
        plan_data['status'] = current_plan.get_status()
        plan_data['days_until_renewal'] = (current_plan.renewal_date - datetime.utcnow()).days
        
        return jsonify({
            'success': True,
            'current_plan': plan_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get current plan: {str(e)}'}), 500

@plan_bp.route('/renew/<user_plan_id>', methods=['POST'])
@jwt_required()
def renew_plan(user_plan_id):
    """Renew a user's plan"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user plan
        user_plan = UserPlan.query.filter_by(
            id=user_plan_id,
            user_id=current_user_id
        ).first()
        
        if not user_plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        data = request.get_json() or {}
        payment_method = data.get('payment_method', 'credit_card')
        
        # Create renewal transaction
        transaction = Transaction(
            user_id=current_user_id,
            plan_id=user_plan.plan_id,
            amount=user_plan.plan.price,
            payment_method=payment_method
        )
        
        db.session.add(transaction)
        db.session.flush()
        
        # Simulate payment processing
        payment_success = True
        
        if payment_success:
            transaction.mark_completed()
            
            # Extend renewal date
            if user_plan.renewal_date < datetime.utcnow():
                # If expired, start from now
                user_plan.renewal_date = datetime.utcnow() + timedelta(days=30)
            else:
                # If not expired, extend from current renewal date
                user_plan.renewal_date += timedelta(days=30)
            
            user_plan.status = 'active'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Plan renewed successfully',
                'transaction': transaction.to_dict(),
                'user_plan': user_plan.to_dict()
            }), 200
        else:
            transaction.mark_failed('Payment processing failed')
            db.session.commit()
            
            return jsonify({
                'error': 'Payment processing failed',
                'transaction': transaction.to_dict()
            }), 402
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Plan renewal failed: {str(e)}'}), 500

@plan_bp.route('/cancel/<user_plan_id>', methods=['POST'])
@jwt_required()
def cancel_plan(user_plan_id):
    """Cancel a user's plan"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user plan
        user_plan = UserPlan.query.filter_by(
            id=user_plan_id,
            user_id=current_user_id
        ).first()
        
        if not user_plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        if user_plan.status == 'cancelled':
            return jsonify({'error': 'Plan is already cancelled'}), 400
        
        # Cancel the plan
        user_plan.status = 'cancelled'
        user_plan.auto_renewal = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plan cancelled successfully',
            'user_plan': user_plan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Plan cancellation failed: {str(e)}'}), 500

@plan_bp.route('/toggle-auto-renewal/<user_plan_id>', methods=['POST'])
@jwt_required()
def toggle_auto_renewal(user_plan_id):
    """Toggle auto-renewal for a user's plan"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user plan
        user_plan = UserPlan.query.filter_by(
            id=user_plan_id,
            user_id=current_user_id
        ).first()
        
        if not user_plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Toggle auto-renewal
        user_plan.auto_renewal = not user_plan.auto_renewal
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Auto-renewal {"enabled" if user_plan.auto_renewal else "disabled"}',
            'auto_renewal': user_plan.auto_renewal,
            'user_plan': user_plan.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to toggle auto-renewal: {str(e)}'}), 500

@plan_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_plan_recommendations():
    """Get plan recommendations for the user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's current plan
        current_plan = user.get_current_plan()
        
        # Simple recommendation logic
        recommendations = []
        
        if current_plan:
            # Recommend plans in the same category with higher features
            same_category_plans = Plan.query.filter(
                Plan.category == current_plan.plan.category,
                Plan.price > current_plan.plan.price,
                Plan.is_available == True,
                Plan.id != current_plan.plan_id
            ).order_by(Plan.price.asc()).limit(3).all()
            
            recommendations.extend(same_category_plans)
            
            # Recommend popular plans from other categories
            other_category_plans = Plan.query.filter(
                Plan.category != current_plan.plan.category,
                Plan.is_popular == True,
                Plan.is_available == True
            ).limit(2).all()
            
            recommendations.extend(other_category_plans)
        else:
            # For users without plans, recommend popular plans
            popular_plans = Plan.query.filter_by(
                is_popular=True,
                is_available=True
            ).order_by(Plan.price.asc()).limit(5).all()
            
            recommendations.extend(popular_plans)
        
        return jsonify({
            'success': True,
            'recommendations': [plan.to_dict() for plan in recommendations],
            'count': len(recommendations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500
