import stripe
from flask import current_app, request, jsonify, render_template
from models import db, User, Subscription, PaymentHistory
import os
from datetime import datetime, timedelta

# Initialize Stripe with your API key (set in the main app)
SUBSCRIPTION_PRICE = 9.99  # $9.99 for 60 days

def init_stripe(app):
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    
def create_checkout_session(user_id):
    """Create a Stripe checkout session for the user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        success_url = request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.host_url + 'payment/cancel'
        
        # Create a checkout session for a one-time payment
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Eviction Timeline Calculator - 60 Day Access',
                        'description': 'Access to the Eviction Timeline Calculator for 60 days',
                    },
                    'unit_amount': int(SUBSCRIPTION_PRICE * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user_id),  # To identify the user after payment
            metadata={
                'user_id': user_id
            }
        )
        
        return checkout_session, None
    except Exception as e:
        return None, str(e)

def handle_checkout_success(session_id):
    """Process a successful checkout and update the user's subscription"""
    try:
        # Retrieve the session details from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status != 'paid':
            return False, "Payment not completed"
        
        # Get user ID from the session
        user_id = int(checkout_session.client_reference_id)
        user = User.query.get(user_id)
        
        if not user:
            return False, "User not found"
        
        # Check if user already has a subscription
        if user.subscription:
            # If the subscription is still active, extend it
            if user.subscription.is_active():
                current_end_date = user.subscription.end_date
                user.subscription.end_date = current_end_date + timedelta(days=60)
            else:
                # If expired, set a new start and end date
                user.subscription.start_date = datetime.utcnow()
                user.subscription.end_date = datetime.utcnow() + timedelta(days=60)
            
            user.subscription.stripe_payment_id = checkout_session.payment_intent
        else:
            # Create a new subscription
            subscription = Subscription(
                user_id=user_id,
                stripe_payment_id=checkout_session.payment_intent,
                days=60
            )
            db.session.add(subscription)
        
        # Record the payment in history
        payment = PaymentHistory(
            user_id=user_id,
            stripe_payment_id=checkout_session.payment_intent,
            amount=SUBSCRIPTION_PRICE,
            currency='USD'
        )
        db.session.add(payment)
        db.session.commit()
        
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_subscription_status(user_id):
    """Get the current subscription status for a user"""
    user = User.query.get(user_id)
    if not user or not user.subscription:
        return {
            'has_subscription': False,
            'days_remaining': 0
        }
    
    return {
        'has_subscription': user.subscription.is_active(),
        'days_remaining': user.subscription.days_remaining(),
        'start_date': user.subscription.start_date.strftime('%Y-%m-%d'),
        'end_date': user.subscription.end_date.strftime('%Y-%m-%d')
    } 