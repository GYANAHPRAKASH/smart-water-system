from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from . import mongo
from .models import User

auth = Blueprint('auth', __name__)

@auth.route("/")
def index():
    return render_template('landing.html')

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard')) # Or admin.dashboard based on role
    
    if request.method == 'POST':
        # Simple extraction for now, will add WTForms later if needed or just use raw form data
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        door_no = request.form.get('door_no')
        colony = request.form.get('colony')
        
        # Check if user exists
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'door_no': door_no,
            'colony': colony,
            'role': 'user',
            'status': 'pending',
            'password_hash': User.generate_hash(password),
            'credits': 0
        }
        mongo.db.users.insert_one(new_user_data)
        flash('Your account has been created! You can login after admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
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
                else:
                     return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')
        else:
            flash('Account not found! If your account was deleted, please contact cityadmin@aquaflow.com or +91 98765 43210.', 'danger')
            
    return render_template('login.html')

@auth.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
