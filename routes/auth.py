from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
import uuid
import secrets

from app import db, bcrypt
from models.user import User, UserProfile, RefreshToken
from forms.auth import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm, ProfileForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            if user.status != 'active':
                flash('Your account is not active. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)
                
            login_user(user, remember=form.remember.data)
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', form=form)
            
        user = User(
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='landlord'  # Default role for new registrations
        )
        
        profile = UserProfile(user=user)
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        # TODO: Send verification email
        
        flash('Account created successfully! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)
    
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            # TODO: Generate reset token and send email
            pass
            
        # Always show success message to prevent email enumeration
        flash('If your email is registered, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', form=form)
    
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    # TODO: Validate reset token
    user = None
    
    if not user:
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)
    
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    profile = user.profile or UserProfile(user=user)
    
    form = ProfileForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        
        # Update profile
        profile.company_name = form.company_name.data
        profile.address = form.address.data
        profile.city = form.city.data
        profile.state = form.state.data
        profile.zip_code = form.zip_code.data
        profile.country = form.country.data
        profile.bio = form.bio.data
        
        # Handle profile picture upload
        if form.profile_picture.data:
            # TODO: Process and save profile picture
            pass
            
        db.session.add(profile)
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
        
    # Populate form with profile data
    if profile.id:
        form.company_name.data = profile.company_name
        form.address.data = profile.address
        form.city.data = profile.city
        form.state.data = profile.state
        form.zip_code.data = profile.zip_code
        form.country.data = profile.country
        form.bio.data = profile.bio
        
    return render_template('auth/profile.html', form=form, user=user, profile=profile)
    
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect', 'danger')
            
    return render_template('auth/change_password.html', form=form)
    
@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    # TODO: Implement email verification
    
    flash('Your email has been verified. You can now login.', 'success')
    return redirect(url_for('auth.login'))

# API Routes
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
        
    user = User.query.filter_by(email=email.lower()).first()
    
    if not user or not user.check_password(password):
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
    if user.status != 'active':
        return jsonify({'status': 'error', 'message': 'Account is not active'}), 403
        
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    # Generate tokens
    access_token_expires = timedelta(hours=1)
    refresh_token_expires = timedelta(days=30)
    
    # Create refresh token
    token = secrets.token_hex(32)
    refresh_token = RefreshToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + refresh_token_expires
    )
    
    db.session.add(refresh_token)
    db.session.commit()
    
    # TODO: Generate JWT access token
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'data': {
            'user': user.to_dict(),
            'access_token': 'jwt_access_token_here',
            'refresh_token': token,
            'expires_in': int(access_token_expires.total_seconds())
        }
    }), 200

@auth_bp.route('/api/refresh', methods=['POST'])
def api_refresh_token():
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
        
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'status': 'error', 'message': 'Refresh token is required'}), 400
        
    token = RefreshToken.query.filter_by(token=refresh_token).first()
    
    if not token or not token.is_valid():
        return jsonify({'status': 'error', 'message': 'Invalid or expired refresh token'}), 401
        
    user = User.query.get(token.user_id)
    
    if not user or user.status != 'active':
        return jsonify({'status': 'error', 'message': 'User account is not active'}), 403
        
    # Generate new access token
    access_token_expires = timedelta(hours=1)
    
    # TODO: Generate JWT access token
    
    return jsonify({
        'status': 'success',
        'message': 'Token refreshed',
        'data': {
            'access_token': 'new_jwt_access_token_here',
            'expires_in': int(access_token_expires.total_seconds())
        }
    }), 200 