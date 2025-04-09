from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import datetime
import os
import json
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
import stripe

from models import db, User, Subscription, PaymentHistory
from forms import LoginForm, RegistrationForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing-only'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///eviction_calculator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_your_stripe_key'
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_your_stripe_key'

# Initialize Stripe directly
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Initialize extensions
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Create database tables within application context
with app.app_context():
    db.create_all()

# Average timelines based on our analysis (in days) for different counties
# For now, we only have Fulton County data
TIMELINES = {
    "ga": {
        "fulton-ga": {
            "filing_to_judgment": 30,  # Typical time from filing to judgment
            "judgment_to_eviction": 45,  # Typical time from judgment to actual eviction
            "writ_to_eviction": 30,     # Typical time from writ of possession to eviction
        },
        # Default values for Georgia counties (based on Fulton)
        "default": {
            "filing_to_judgment": 30,
            "judgment_to_eviction": 45,
            "writ_to_eviction": 30,
        }
    },
    # Default values for other states (using Georgia's values as baseline)
    "default": {
        "filing_to_judgment": 30,
        "judgment_to_eviction": 45,
        "writ_to_eviction": 30,
    }
}

@app.route('/')
def index():
    if current_user.is_authenticated:
        try:
            # Create subscription status without relying on payment module
            subscription_status = {
                'has_subscription': current_user.has_active_subscription(),
                'days_remaining': current_user.subscription.days_remaining() if current_user.has_active_subscription() else 0
            }
            
            if current_user.has_active_subscription():
                subscription_status['start_date'] = current_user.subscription.start_date.strftime('%Y-%m-%d')
                subscription_status['end_date'] = current_user.subscription.end_date.strftime('%Y-%m-%d')
        except Exception as e:
            print("Error in index route:", str(e))
            subscription_status = {
                'has_subscription': False,
                'days_remaining': 0
            }
            
        return render_template('index.html', user=current_user, subscription=subscription_status)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/subscribe')
@login_required
def subscribe():
    # Check if user already has an active subscription
    if current_user.has_active_subscription():
        flash('You already have an active subscription!')
        return redirect(url_for('index'))
    
    try:
        # Create a Stripe checkout session directly
        
        # Set the price for subscription (60 days)
        SUBSCRIPTION_PRICE = 9.99
        
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
            client_reference_id=str(current_user.id),  # To identify the user after payment
            metadata={
                'user_id': current_user.id
            }
        )
        
        # Redirect to Stripe checkout
        return render_template('checkout.html', 
                            checkout_session_id=checkout_session.id,
                            stripe_public_key=app.config['STRIPE_PUBLIC_KEY'])
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        flash(f'Error creating checkout session: {str(e)}')
        return redirect(url_for('index'))

@app.route('/payment/success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        flash('Invalid payment session')
        return redirect(url_for('index'))
    
    try:
        # Process successful checkout directly
        from datetime import timedelta
        
        # Retrieve the session details from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status != 'paid':
            flash('Payment not completed')
            return redirect(url_for('index'))
        
        # Get user ID from the session
        user_id = int(checkout_session.client_reference_id)
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found')
            return redirect(url_for('index'))
        
        # Check if user already has a subscription
        if hasattr(user, 'subscription') and user.subscription:
            # If the subscription is still active, extend it
            if user.subscription.is_active():
                current_end_date = user.subscription.end_date
                user.subscription.end_date = current_end_date + timedelta(days=60)
            else:
                # If expired, set a new start and end date
                user.subscription.start_date = datetime.datetime.utcnow()
                user.subscription.end_date = datetime.datetime.utcnow() + timedelta(days=60)
            
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
        payment_record = PaymentHistory(
            user_id=user_id,
            stripe_payment_id=checkout_session.payment_intent,
            amount=9.99,  # Hardcoded price
            currency='USD'
        )
        db.session.add(payment_record)
        db.session.commit()
        
        flash('Payment successful! Your subscription is now active.')
    except Exception as e:
        db.session.rollback()
        print(f"Error processing payment: {str(e)}")
        flash(f'Error processing payment: {str(e)}')
    
    return redirect(url_for('account'))

@app.route('/payment/cancel')
@login_required
def payment_cancel():
    flash('Payment was cancelled.')
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    try:
        # Create subscription status without relying on payment module
        subscription_status = {
            'has_subscription': current_user.has_active_subscription(),
            'days_remaining': current_user.subscription.days_remaining() if current_user.has_active_subscription() else 0
        }
        
        if current_user.has_active_subscription():
            subscription_status['start_date'] = current_user.subscription.start_date.strftime('%Y-%m-%d')
            subscription_status['end_date'] = current_user.subscription.end_date.strftime('%Y-%m-%d')
    except Exception as e:
        print("Error in account route:", str(e))
        subscription_status = {
            'has_subscription': False,
            'days_remaining': 0
        }
    
    payment_history = PaymentHistory.query.filter_by(user_id=current_user.id).order_by(PaymentHistory.payment_date.desc()).all()
    
    return render_template('account.html', 
                          user=current_user, 
                          subscription=subscription_status,
                          payment_history=payment_history)

@app.route('/dashboard')
@login_required
def dashboard():
    # The dashboard route will provide user subscription and account information
    try:
        # Debug - print information about the payment module
        print("Payment module type:", type(stripe))
        print("Payment module dir:", dir(stripe))
        
        # Try to access the function directly
        subscription_status = {
            'has_subscription': current_user.has_active_subscription(),
            'days_remaining': current_user.subscription.days_remaining() if current_user.has_active_subscription() else 0
        }
        
        if current_user.has_active_subscription():
            subscription_status['start_date'] = current_user.subscription.start_date.strftime('%Y-%m-%d')
            subscription_status['end_date'] = current_user.subscription.end_date.strftime('%Y-%m-%d')
    except Exception as e:
        print("Error getting subscription status:", str(e))
        subscription_status = {
            'has_subscription': False,
            'days_remaining': 0
        }
    
    return render_template('dashboard.html', 
                          user=current_user, 
                          subscription_active=subscription_status.get('has_subscription', False),
                          subscription_type=getattr(current_user, 'subscription', None),
                          days_remaining=subscription_status.get('days_remaining', 0))

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Check if user is logged in and has an active subscription
        if current_user.is_authenticated:
            if not current_user.has_active_subscription():
                return jsonify({"error": "You need an active subscription to use this feature. Please subscribe."}), 403
        else:
            # For non-logged in users, redirect to login
            return jsonify({"error": "Please login to use this feature."}), 401
        
        # Get the data from the form
        state = request.form.get('state', 'ga')
        county = request.form.get('county', 'fulton-ga')
        filing_date_str = request.form.get('filing_date')
        writ_date_str = request.form.get('writ_date')
        
        # Get the appropriate timeline data based on state and county
        if state in TIMELINES and county in TIMELINES[state]:
            timeline_data = TIMELINES[state][county]
        elif state in TIMELINES:
            # Use state default if county isn't available
            timeline_data = TIMELINES[state]["default"]
        else:
            # Use global default if state isn't available
            timeline_data = TIMELINES["default"]
        
        # Parse dates
        filing_date = datetime.datetime.strptime(filing_date_str, '%Y-%m-%d').date() if filing_date_str else None
        writ_date = datetime.datetime.strptime(writ_date_str, '%Y-%m-%d').date() if writ_date_str else None
        
        today = datetime.date.today()
        result = {
            "state": state,
            "county": county
        }
        
        # Calculate based on available dates
        if filing_date and writ_date:
            # If we have both filing date and writ date
            days_to_writ = (writ_date - filing_date).days
            estimated_eviction_date = writ_date + datetime.timedelta(days=timeline_data["writ_to_eviction"])
            days_remaining = (estimated_eviction_date - today).days if estimated_eviction_date > today else 0
            
            result.update({
                "filing_date": filing_date.strftime('%Y-%m-%d'),
                "writ_date": writ_date.strftime('%Y-%m-%d'),
                "days_to_writ": days_to_writ,
                "estimated_eviction_date": estimated_eviction_date.strftime('%Y-%m-%d'),
                "days_remaining": days_remaining,
                "total_process_days": (estimated_eviction_date - filing_date).days,
                "timeline_used": f"{county if county in TIMELINES.get(state, {}) else 'default'}"
            })
        elif filing_date:
            # If we only have filing date
            estimated_judgment_date = filing_date + datetime.timedelta(days=timeline_data["filing_to_judgment"])
            estimated_eviction_date = estimated_judgment_date + datetime.timedelta(days=timeline_data["judgment_to_eviction"])
            days_remaining = (estimated_eviction_date - today).days if estimated_eviction_date > today else 0
            
            result.update({
                "filing_date": filing_date.strftime('%Y-%m-%d'),
                "estimated_judgment_date": estimated_judgment_date.strftime('%Y-%m-%d'),
                "estimated_eviction_date": estimated_eviction_date.strftime('%Y-%m-%d'),
                "days_remaining": days_remaining,
                "total_process_days": (estimated_eviction_date - filing_date).days,
                "timeline_used": f"{county if county in TIMELINES.get(state, {}) else 'default'}"
            })
        elif writ_date:
            # If we only have writ date
            estimated_eviction_date = writ_date + datetime.timedelta(days=timeline_data["writ_to_eviction"])
            days_remaining = (estimated_eviction_date - today).days if estimated_eviction_date > today else 0
            
            result.update({
                "writ_date": writ_date.strftime('%Y-%m-%d'),
                "estimated_eviction_date": estimated_eviction_date.strftime('%Y-%m-%d'),
                "days_remaining": days_remaining,
                "from_writ_to_eviction": timeline_data["writ_to_eviction"],
                "timeline_used": f"{county if county in TIMELINES.get(state, {}) else 'default'}"
            })
        else:
            return jsonify({"error": "Please provide at least one date"}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/payment')
def payment():
    # Redirect to subscribe for backward compatibility
    return redirect(url_for('subscribe'))

# Create the templates directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

if __name__ == '__main__':
    app.run(debug=True) 