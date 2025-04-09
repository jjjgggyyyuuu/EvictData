from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.relationship('Subscription', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_active_subscription(self):
        if not self.subscription:
            return False
        return self.subscription.is_active()
    
    def is_subscription_active(self):
        return self.has_active_subscription()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(120), nullable=True)
    stripe_payment_id = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_trial = db.Column(db.Boolean, default=False)
    
    def __init__(self, user_id, stripe_customer_id=None, stripe_payment_id=None, days=60, is_trial=False):
        self.user_id = user_id
        self.stripe_customer_id = stripe_customer_id
        self.stripe_payment_id = stripe_payment_id
        self.start_date = datetime.utcnow()
        self.end_date = self.start_date + timedelta(days=days)
        self.is_trial = is_trial
    
    def is_active(self):
        return self.end_date > datetime.utcnow()
    
    def days_remaining(self):
        if not self.is_active():
            return 0
        delta = self.end_date - datetime.utcnow()
        return delta.days
    
    def __repr__(self):
        return f'<Subscription {self.id} - User {self.user_id}>'

class PaymentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.id} - User {self.user_id}>' 