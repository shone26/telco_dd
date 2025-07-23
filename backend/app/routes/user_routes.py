from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, UserPlan, Transaction

user_bp = Blueprint('users', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get detailed user profile with plans and payment history"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's current plan
        current_plan = user.get_current_plan()
        current_plan_data = None
        if current_plan:
            current_plan_data = {
                'id': current_plan.id,
                'plan_id': current_plan.plan_id,
                'plan_name': current_plan.plan.name,
                'plan_category': current_plan.plan.category,
                'activation_date': current_plan.activation_date.isoformat(),
                'renewal_date': current_plan.renewal_date.isoformat(),
                'status': current_plan.get_status(),
                'auto_renewal': current_plan.auto_renewal,
                'price': current_plan.plan.price,
                'days_until_renewal': (current_plan.renewal_date - db.func.now()).days if current_plan.renewal_date else None
            }
        
        # Get recent payment history
        recent_payments = user.get_payment_history(limit=5)
        payment_history = [transaction.to_dict() for transaction in recent_payments]
        
        # Get all user plans
        all_plans = UserPlan.query.filter_by(user_id=int(current_user_id)).order_by(
            UserPlan.created_at.desc()
        ).limit(10).all()
        
        plans_history = []
        for plan in all_plans:
            plan_data = plan.to_dict()
            plan_data['status'] = plan.get_status()
            plans_history.append(plan_data)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'created_at': user.created_at.isoformat(),
                'is_active': user.is_active,
                'current_plan': current_plan_data,
                'payment_history': payment_history,
                'plans_history': plans_history
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user profile: {str(e)}'}), 500

@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_user_dashboard():
    """Get user dashboard data"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current plan
        current_plan = user.get_current_plan()
        
        # Get payment statistics
        total_spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == int(current_user_id),
            Transaction.status == 'completed',
            Transaction.amount > 0
        ).scalar() or 0
        
        total_transactions = Transaction.query.filter_by(
            user_id=int(current_user_id),
            status='completed'
        ).count()
        
        # Get active plans count
        active_plans_count = UserPlan.query.filter_by(
            user_id=int(current_user_id),
            status='active'
        ).count()
        
        # Get expiring plans (within 7 days)
        from datetime import datetime, timedelta
        expiring_soon = UserPlan.query.filter(
            UserPlan.user_id == int(current_user_id),
            UserPlan.status == 'active',
            UserPlan.renewal_date <= datetime.utcnow() + timedelta(days=7),
            UserPlan.renewal_date > datetime.utcnow()
        ).all()
        
        expiring_plans = []
        for plan in expiring_soon:
            expiring_plans.append({
                'id': plan.id,
                'plan_name': plan.plan.name,
                'renewal_date': plan.renewal_date.isoformat(),
                'days_until_renewal': (plan.renewal_date - datetime.utcnow()).days,
                'price': plan.plan.price
            })
        
        # Get recent activity
        recent_transactions = Transaction.query.filter_by(
            user_id=int(current_user_id)
        ).order_by(Transaction.created_at.desc()).limit(5).all()
        
        dashboard_data = {
            'user': {
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'member_since': user.created_at.isoformat()
            },
            'current_plan': current_plan.to_dict() if current_plan else None,
            'statistics': {
                'total_spent': total_spent,
                'total_transactions': total_transactions,
                'active_plans': active_plans_count
            },
            'expiring_plans': expiring_plans,
            'recent_activity': [transaction.to_dict() for transaction in recent_transactions]
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard data: {str(e)}'}), 500

@user_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """Get user notifications"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        notifications = []
        
        # Check for expiring plans
        from datetime import datetime, timedelta
        expiring_plans = UserPlan.query.filter(
            UserPlan.user_id == current_user_id,
            UserPlan.status == 'active',
            UserPlan.renewal_date <= datetime.utcnow() + timedelta(days=7),
            UserPlan.renewal_date > datetime.utcnow()
        ).all()
        
        for plan in expiring_plans:
            days_left = (plan.renewal_date - datetime.utcnow()).days
            notifications.append({
                'id': f"expiring_{plan.id}",
                'type': 'warning',
                'title': 'Plan Expiring Soon',
                'message': f'Your {plan.plan.name} plan expires in {days_left} days',
                'action_url': f'/plans/renew/{plan.id}',
                'action_text': 'Renew Now',
                'created_at': datetime.utcnow().isoformat()
            })
        
        # Check for expired plans
        expired_plans = UserPlan.query.filter(
            UserPlan.user_id == current_user_id,
            UserPlan.status == 'active',
            UserPlan.renewal_date < datetime.utcnow()
        ).all()
        
        for plan in expired_plans:
            notifications.append({
                'id': f"expired_{plan.id}",
                'type': 'error',
                'title': 'Plan Expired',
                'message': f'Your {plan.plan.name} plan has expired',
                'action_url': f'/plans/renew/{plan.id}',
                'action_text': 'Renew Now',
                'created_at': datetime.utcnow().isoformat()
            })
        
        # Check for failed payments
        failed_payments = Transaction.query.filter(
            Transaction.user_id == current_user_id,
            Transaction.status == 'failed',
            Transaction.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        for payment in failed_payments:
            notifications.append({
                'id': f"failed_payment_{payment.id}",
                'type': 'error',
                'title': 'Payment Failed',
                'message': f'Payment of ₹{payment.amount} failed: {payment.failure_reason}',
                'action_url': f'/payments/retry/{payment.id}',
                'action_text': 'Retry Payment',
                'created_at': payment.created_at.isoformat()
            })
        
        # Sort notifications by creation date (newest first)
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get notifications: {str(e)}'}), 500

@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_user_preferences():
    """Get user preferences"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # For now, return default preferences
        # In a real application, these would be stored in a separate table
        preferences = {
            'notifications': {
                'email_notifications': True,
                'sms_notifications': True,
                'renewal_reminders': True,
                'promotional_offers': False
            },
            'payment': {
                'auto_renewal': True,
                'preferred_payment_method': 'credit_card'
            },
            'privacy': {
                'data_sharing': False,
                'marketing_communications': False
            }
        }
        
        return jsonify({
            'success': True,
            'preferences': preferences
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get preferences: {str(e)}'}), 500

@user_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_user_preferences():
    """Update user preferences"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No preferences data provided'}), 400
        
        # In a real application, preferences would be stored in database
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update preferences: {str(e)}'}), 500

@user_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_user_activity():
    """Get user activity log"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        activity_type = request.args.get('type')  # transaction, plan, profile
        
        activities = []
        
        # Get transaction activities
        if not activity_type or activity_type == 'transaction':
            transactions = Transaction.query.filter_by(
                user_id=current_user_id
            ).order_by(Transaction.created_at.desc()).limit(limit).all()
            
            for transaction in transactions:
                activities.append({
                    'id': f"transaction_{transaction.id}",
                    'type': 'transaction',
                    'title': f"Payment {transaction.status.title()}",
                    'description': f"₹{transaction.amount} for {transaction.plan.name}",
                    'status': transaction.status,
                    'timestamp': transaction.created_at.isoformat(),
                    'details': transaction.to_dict()
                })
        
        # Get plan activities
        if not activity_type or activity_type == 'plan':
            user_plans = UserPlan.query.filter_by(
                user_id=current_user_id
            ).order_by(UserPlan.created_at.desc()).limit(limit).all()
            
            for plan in user_plans:
                activities.append({
                    'id': f"plan_{plan.id}",
                    'type': 'plan',
                    'title': f"Plan {plan.status.title()}",
                    'description': f"{plan.plan.name} - {plan.plan.category}",
                    'status': plan.status,
                    'timestamp': plan.created_at.isoformat(),
                    'details': plan.to_dict()
                })
        
        # Sort activities by timestamp (newest first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit results
        activities = activities[:limit]
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user activity: {str(e)}'}), 500

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate various statistics
        from datetime import datetime, timedelta
        
        # Total spending
        total_spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.status == 'completed',
            Transaction.amount > 0
        ).scalar() or 0
        
        # Monthly spending (current month)
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.status == 'completed',
            Transaction.amount > 0,
            Transaction.created_at >= current_month_start
        ).scalar() or 0
        
        # Plan statistics
        total_plans = UserPlan.query.filter_by(user_id=current_user_id).count()
        active_plans = UserPlan.query.filter_by(user_id=current_user_id, status='active').count()
        expired_plans = UserPlan.query.filter_by(user_id=current_user_id, status='expired').count()
        
        # Payment statistics
        total_transactions = Transaction.query.filter_by(user_id=current_user_id).count()
        successful_payments = Transaction.query.filter_by(
            user_id=current_user_id, 
            status='completed'
        ).count()
        failed_payments = Transaction.query.filter_by(
            user_id=current_user_id, 
            status='failed'
        ).count()
        
        # Calculate success rate
        success_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0
        
        # Account age
        account_age_days = (datetime.utcnow() - user.created_at).days
        
        stats = {
            'spending': {
                'total_spent': total_spent,
                'monthly_spent': monthly_spent,
                'average_transaction': total_spent / successful_payments if successful_payments > 0 else 0
            },
            'plans': {
                'total_plans': total_plans,
                'active_plans': active_plans,
                'expired_plans': expired_plans
            },
            'payments': {
                'total_transactions': total_transactions,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'success_rate': round(success_rate, 2)
            },
            'account': {
                'member_since': user.created_at.isoformat(),
                'account_age_days': account_age_days,
                'last_activity': user.updated_at.isoformat() if user.updated_at else user.created_at.isoformat()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user stats: {str(e)}'}), 500

@user_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_user_account():
    """Delete user account (soft delete)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        
        # Verify password for account deletion
        if not password or not user.check_password(password):
            return jsonify({'error': 'Password verification required for account deletion'}), 401
        
        # Cancel all active plans
        active_plans = UserPlan.query.filter_by(
            user_id=current_user_id,
            status='active'
        ).all()
        
        for plan in active_plans:
            plan.status = 'cancelled'
            plan.auto_renewal = False
        
        # Deactivate user account (soft delete)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete account: {str(e)}'}), 500
