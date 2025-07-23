from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Plan, Transaction, UserPlan
from datetime import datetime
import re
import random
import string

payment_bp = Blueprint('payments', __name__)

def validate_credit_card(card_number):
    """Basic credit card validation using Luhn algorithm"""
    card_number = re.sub(r'\D', '', card_number)
    
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Luhn algorithm
    total = 0
    reverse_digits = card_number[::-1]
    
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n = (n // 10) + (n % 10)
        total += n
    
    return total % 10 == 0

def validate_cvv(cvv):
    """Validate CVV format"""
    return re.match(r'^\d{3,4}$', cvv) is not None

def validate_expiry_date(month, year):
    """Validate expiry date"""
    try:
        month = int(month)
        year = int(year)
        
        if month < 1 or month > 12:
            return False
        
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        if year < current_year:
            return False
        
        if year == current_year and month < current_month:
            return False
        
        return True
    except (ValueError, TypeError):
        return False

def simulate_payment_processing(payment_data):
    """Simulate payment gateway processing"""
    # Simulate different payment scenarios for testing
    card_number = payment_data.get('card_number', '')
    
    # Test card numbers for different scenarios
    if card_number.endswith('0000'):
        return {'success': False, 'error': 'Card declined'}
    elif card_number.endswith('1111'):
        return {'success': False, 'error': 'Insufficient funds'}
    elif card_number.endswith('2222'):
        return {'success': False, 'error': 'Card expired'}
    elif card_number.endswith('3333'):
        return {'success': False, 'error': 'Invalid CVV'}
    else:
        # Simulate successful payment
        return {
            'success': True,
            'transaction_id': ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
            'gateway_reference': f"GW_{random.randint(100000, 999999)}"
        }

@payment_bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    """Process payment for a plan subscription or renewal"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No payment data provided'}), 400
        
        # Extract payment information
        plan_id = data.get('plan_id')
        payment_method = data.get('payment_method', 'credit_card')
        card_number = data.get('card_number', '').replace(' ', '')
        card_holder_name = data.get('card_holder_name', '').strip()
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')
        cvv = data.get('cvv', '').strip()
        billing_address = data.get('billing_address', {})
        
        # Validate required fields
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        if payment_method == 'credit_card':
            if not all([card_number, card_holder_name, expiry_month, expiry_year, cvv]):
                return jsonify({'error': 'All card details are required'}), 400
            
            # Validate card details
            if not validate_credit_card(card_number):
                return jsonify({'error': 'Invalid credit card number'}), 400
            
            if not validate_cvv(cvv):
                return jsonify({'error': 'Invalid CVV'}), 400
            
            if not validate_expiry_date(expiry_month, expiry_year):
                return jsonify({'error': 'Invalid or expired card'}), 400
        
        # Get plan details
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_available:
            return jsonify({'error': 'Plan not found or unavailable'}), 404
        
        # Create transaction record
        transaction = Transaction(
            user_id=int(current_user_id),
            plan_id=plan_id,
            amount=plan.price,
            payment_method=payment_method
        )
        
        db.session.add(transaction)
        db.session.flush()  # Get transaction ID
        
        # Process payment through gateway simulation
        payment_result = simulate_payment_processing({
            'card_number': card_number,
            'amount': plan.price,
            'currency': plan.currency
        })
        
        if payment_result['success']:
            # Payment successful
            transaction.mark_completed()
            transaction.transaction_reference = payment_result.get('gateway_reference', transaction.transaction_reference)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment processed successfully',
                'transaction': transaction.to_dict(),
                'gateway_reference': payment_result.get('gateway_reference')
            }), 200
        else:
            # Payment failed
            transaction.mark_failed(payment_result['error'])
            db.session.commit()
            
            return jsonify({
                'success': False,
                'error': payment_result['error'],
                'transaction': transaction.to_dict()
            }), 402
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Payment processing failed: {str(e)}'}), 500

@payment_bp.route('/history', methods=['GET'])
@jwt_required()
def get_payment_history():
    """Get user's payment history"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        status = request.args.get('status')  # completed, failed, pending
        
        # Build query
        query = Transaction.query.filter_by(user_id=int(current_user_id))
        
        if status:
            query = query.filter_by(status=status)
        
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'transactions': [transaction.to_dict() for transaction in transactions],
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get payment history: {str(e)}'}), 500

@payment_bp.route('/transaction/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get specific transaction details"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=int(current_user_id)
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        return jsonify({
            'success': True,
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get transaction: {str(e)}'}), 500

@payment_bp.route('/retry/<transaction_id>', methods=['POST'])
@jwt_required()
def retry_payment(transaction_id):
    """Retry a failed payment"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get original transaction
        original_transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not original_transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        if original_transaction.status != 'failed':
            return jsonify({'error': 'Only failed transactions can be retried'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No payment data provided'}), 400
        
        # Create new transaction for retry
        new_transaction = Transaction(
            user_id=current_user_id,
            plan_id=original_transaction.plan_id,
            amount=original_transaction.amount,
            payment_method=data.get('payment_method', original_transaction.payment_method)
        )
        
        db.session.add(new_transaction)
        db.session.flush()
        
        # Process payment
        payment_result = simulate_payment_processing({
            'card_number': data.get('card_number', ''),
            'amount': new_transaction.amount
        })
        
        if payment_result['success']:
            new_transaction.mark_completed()
            new_transaction.transaction_reference = payment_result.get('gateway_reference', new_transaction.transaction_reference)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment retry successful',
                'transaction': new_transaction.to_dict()
            }), 200
        else:
            new_transaction.mark_failed(payment_result['error'])
            db.session.commit()
            
            return jsonify({
                'success': False,
                'error': payment_result['error'],
                'transaction': new_transaction.to_dict()
            }), 402
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Payment retry failed: {str(e)}'}), 500

@payment_bp.route('/refund/<transaction_id>', methods=['POST'])
@jwt_required()
def request_refund(transaction_id):
    """Request refund for a completed transaction"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        if transaction.status != 'completed':
            return jsonify({'error': 'Only completed transactions can be refunded'}), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'User requested refund')
        
        # In a real application, this would integrate with payment gateway for refund processing
        # For now, we'll simulate the refund process
        
        # Create refund transaction (negative amount)
        refund_transaction = Transaction(
            user_id=current_user_id,
            plan_id=transaction.plan_id,
            amount=-transaction.amount,  # Negative amount for refund
            payment_method=transaction.payment_method
        )
        refund_transaction.status = 'completed'
        refund_transaction.transaction_reference = f"REFUND_{transaction.transaction_reference}"
        
        db.session.add(refund_transaction)
        
        # Update original transaction status
        transaction.status = 'refunded'
        
        # Cancel associated user plan if exists
        user_plan = UserPlan.query.filter_by(
            user_id=current_user_id,
            plan_id=transaction.plan_id
        ).order_by(UserPlan.created_at.desc()).first()
        
        if user_plan and user_plan.status == 'active':
            user_plan.status = 'cancelled'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Refund processed successfully',
            'refund_transaction': refund_transaction.to_dict(),
            'original_transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Refund processing failed: {str(e)}'}), 500

@payment_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """Get available payment methods"""
    try:
        payment_methods = [
            {
                'id': 'credit_card',
                'name': 'Credit Card',
                'description': 'Visa, MasterCard, American Express',
                'icon': 'credit-card',
                'enabled': True
            },
            {
                'id': 'debit_card',
                'name': 'Debit Card',
                'description': 'Bank debit cards',
                'icon': 'debit-card',
                'enabled': True
            },
            {
                'id': 'upi',
                'name': 'UPI',
                'description': 'Google Pay, PhonePe, Paytm',
                'icon': 'upi',
                'enabled': True
            },
            {
                'id': 'net_banking',
                'name': 'Net Banking',
                'description': 'All major banks',
                'icon': 'bank',
                'enabled': True
            },
            {
                'id': 'wallet',
                'name': 'Digital Wallet',
                'description': 'Paytm, Amazon Pay, etc.',
                'icon': 'wallet',
                'enabled': True
            }
        ]
        
        return jsonify({
            'success': True,
            'payment_methods': payment_methods
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get payment methods: {str(e)}'}), 500

@payment_bp.route('/validate-card', methods=['POST'])
def validate_card():
    """Validate credit card details"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No card data provided'}), 400
        
        card_number = data.get('card_number', '').replace(' ', '')
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')
        cvv = data.get('cvv', '').strip()
        
        validation_result = {
            'valid': True,
            'errors': []
        }
        
        # Validate card number
        if not validate_credit_card(card_number):
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid credit card number')
        
        # Validate expiry date
        if not validate_expiry_date(expiry_month, expiry_year):
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid or expired card')
        
        # Validate CVV
        if not validate_cvv(cvv):
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid CVV')
        
        # Determine card type
        card_type = 'unknown'
        if card_number.startswith('4'):
            card_type = 'visa'
        elif card_number.startswith(('5', '2')):
            card_type = 'mastercard'
        elif card_number.startswith('3'):
            card_type = 'amex'
        
        validation_result['card_type'] = card_type
        
        return jsonify({
            'success': True,
            'validation': validation_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Card validation failed: {str(e)}'}), 500

@payment_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_payment_summary():
    """Get payment summary for the user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get payment statistics
        total_transactions = Transaction.query.filter_by(user_id=current_user_id).count()
        completed_transactions = Transaction.query.filter_by(
            user_id=current_user_id, 
            status='completed'
        ).count()
        failed_transactions = Transaction.query.filter_by(
            user_id=current_user_id, 
            status='failed'
        ).count()
        
        # Calculate total amount spent
        total_spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user_id,
            Transaction.status == 'completed',
            Transaction.amount > 0  # Exclude refunds
        ).scalar() or 0
        
        # Get recent transactions
        recent_transactions = Transaction.query.filter_by(
            user_id=current_user_id
        ).order_by(Transaction.created_at.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_transactions': total_transactions,
                'completed_transactions': completed_transactions,
                'failed_transactions': failed_transactions,
                'total_spent': total_spent,
                'success_rate': (completed_transactions / total_transactions * 100) if total_transactions > 0 else 0
            },
            'recent_transactions': [transaction.to_dict() for transaction in recent_transactions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get payment summary: {str(e)}'}), 500
