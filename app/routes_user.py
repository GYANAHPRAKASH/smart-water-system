from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from . import db
from .models import User, Complaint, Schedule
from .ai_module import analyze_complaint
from datetime import datetime

user = Blueprint('user', __name__)

@user.route("/user/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
        
    my_complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    # Filter schedules for the user's colony
    # In a real app, we might want to filter by date too.
    schedules = Schedule.query.filter_by(colony=current_user.colony).order_by(Schedule.date_time.desc()).all()
    
    # Serialize schedules for JS calendar
    schedules_data = [{
        'colony': s.colony,
         'action': s.action,
         'notes': s.notes,
         'date_time': s.date_time.isoformat(),
         'time_str': s.date_time.strftime("%I:%M %p")
    } for s in schedules]
    
    return render_template('user_dashboard.html', complaints=my_complaints, schedules=schedules, schedules_data=schedules_data)

@user.route("/user/submit_complaint", methods=['POST'])
@login_required
def submit_complaint():
    type = request.form.get('type')
    description = request.form.get('description')
    
    # AI Logic
    priority = analyze_complaint(description)
    
    new_complaint = Complaint(user_id=current_user.id, type=type, description=description, priority=priority)
    db.session.add(new_complaint)
    db.session.commit()
    
    flash(f'Complaint Submitted. Priority set to {priority} based on analysis.', 'success')
    return redirect(url_for('user.dashboard'))
