# pyre-ignore-all-errors
from flask import Blueprint, render_template, url_for, flash, redirect, request, session, current_app
from flask_login import login_user, current_user, logout_user, login_required
from . import mongo, oauth
from .models import User
from .mail_service import send_registration_pending, send_account_approved

auth = Blueprint('auth', __name__)

# ── Landing ────────────────────────────────────────────────────────

@auth.route("/")
def index():
    return render_template('landing.html')

# ── Register ───────────────────────────────────────────────────────

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username   = request.form.get('username')
        password   = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name  = request.form.get('last_name')
        email      = request.form.get('email', '').strip().lower()
        phone      = request.form.get('phone')
        door_no    = request.form.get('door_no')
        colony     = request.form.get('colony')

        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))

        new_user_data = {
            'username':      username,
            'first_name':    first_name,
            'last_name':     last_name,
            'email':         email,
            'phone':         phone,
            'door_no':       door_no,
            'colony':        colony,
            'role':          'user',
            'status':        'pending',
            'password_hash': User.generate_hash(password),
            'credits':       0
        }
        mongo.db.users.insert_one(new_user_data)

        # Send pending email
        send_registration_pending(email, username)

        flash('Account created! You can login after admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ── Login ──────────────────────────────────────────────────────────

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = mongo.db.users.find_one({'username': username})

        if user_data:
            user = User(user_data)
            if user.check_password(password):
                if user.role == 'user' and user.status != 'approved':
                    flash('Your account is pending approval or inactive. Please contact admin at cityadmin@aquaflow.com.', 'warning')
                    return redirect(url_for('auth.login'))
                login_user(user)
                next_page = request.args.get('next')
                if user.role == 'admin':
                    return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
                return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
        else:
            flash('Account not found! Contact cityadmin@aquaflow.com or +91 98765 43210.', 'danger')

    return render_template('login.html')

# ── Logout ─────────────────────────────────────────────────────────

@auth.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# ── Change Password ────────────────────────────────────────────────

@auth.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password     = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user_data = mongo.db.users.find_one({'username': current_user.username})
        user = User(user_data)
        if not user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))

        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'warning')
            return redirect(url_for('auth.change_password'))

        new_hash = User.generate_hash(new_password)
        mongo.db.users.update_one(
            {'username': current_user.username},
            {'$set': {'password_hash': new_hash}}
        )
        flash('Password updated successfully!', 'success')
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('change_password.html')

# ── Google OAuth ───────────────────────────────────────────────────

@auth.route("/auth/google")
def google_login():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google login is not configured yet. Please use email/password login.', 'warning')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth.route("/auth/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    userinfo = token.get('userinfo')
    if not userinfo:
        flash('Could not retrieve Google profile. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    google_id  = userinfo.get('sub')
    email      = userinfo.get('email', '').lower()
    first_name = userinfo.get('given_name', '')
    last_name  = userinfo.get('family_name', '')

    # 1. Check if user already exists by google_id
    user_data = mongo.db.users.find_one({'google_id': google_id})

    # 2. Or by email (user may have registered manually before)
    if not user_data and email:
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            # Link Google ID to existing account
            mongo.db.users.update_one({'_id': user_data['_id']}, {'$set': {'google_id': google_id}})
            user_data = mongo.db.users.find_one({'_id': user_data['_id']})

    # 3. Brand-new Google user — create with pending status
    if not user_data:
        username = email.split('@')[0].replace('.', '_')
        # Ensure unique username
        base = username
        counter = 1
        while mongo.db.users.find_one({'username': username}):
            username = f"{base}{counter}"
            counter += 1

        new_user = {
            'username':      username,
            'first_name':    first_name,
            'last_name':     last_name,
            'email':         email,
            'google_id':     google_id,
            'role':          'user',
            'status':        'pending',
            'credits':       0,
            'phone':         None,
            'door_no':       None,
            'colony':        None,
        }
        result = mongo.db.users.insert_one(new_user)
        user_data = mongo.db.users.find_one({'_id': result.inserted_id})

    user = User(user_data)

    # Check account status
    if user.role == 'user' and user.status != 'approved' and user.profile_complete:
        flash('Your account is pending admin approval. You\'ll receive an email when approved.', 'warning')
        return redirect(url_for('auth.login'))

    login_user(user)

    # New Google user — needs to complete profile before accessing dashboard
    if not user.profile_complete:
        flash('Welcome! Please complete your profile to continue.', 'info')
        return redirect(url_for('auth.complete_profile'))

    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('user.dashboard'))

# ── Complete Profile (for new Google users) ────────────────────────

@auth.route("/complete_profile", methods=['GET', 'POST'])
@login_required
def complete_profile():
    # If profile already complete, redirect away
    if current_user.profile_complete:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        phone   = request.form.get('phone')
        door_no = request.form.get('door_no')
        colony  = request.form.get('colony')

        mongo.db.users.update_one(
            {'username': current_user.username},
            {'$set': {'phone': phone, 'door_no': door_no, 'colony': colony}}
        )

        # Send pending email now that we have full info
        send_registration_pending(current_user.email, current_user.username)

        flash('Profile completed! Your account is pending admin approval. You\'ll be notified by email.', 'success')
        logout_user()
        return redirect(url_for('auth.login'))

    return render_template('complete_profile.html')
