from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from . import db
from .models import User, Complaint, Schedule
from datetime import datetime
from .ai_module import analyze_complaint, generate_simulated_data, predict_demand, detect_anomalies

admin = Blueprint('admin', __name__)

@admin.route("/admin/dashboard")
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access Denied: You are not an admin.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Generate simulated data for demo
    generate_simulated_data('Admin Office') # Using Admin's colony for demo
    
    # AI Analysis
    predictions = predict_demand('Admin Office')
    anomalies = detect_anomalies('Admin Office')
    
    users = User.query.all()
    pending_users = User.query.filter_by(status='pending').all()
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    schedules = Schedule.query.order_by(Schedule.date_time.desc()).all()
    
    # Serialize schedules for JS calendar
    schedules_data = [{
        'colony': s.colony,
         'action': s.action,
         'notes': s.notes,
         'date_time': s.date_time.isoformat(),
         'time_str': s.date_time.strftime("%I:%M %p")
    } for s in schedules]
    
    return render_template('admin_dashboard.html', 
                           users=users, 
                           pending_users=pending_users, 
                           complaints=complaints, 
                           schedules=schedules,
                           schedules_data=schedules_data,
                           predictions=predictions,
                           anomalies=anomalies)

@admin.route("/admin/approve_user/<int:user_id>")
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.status = 'approved'
    db.session.commit()
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/reject_user/<int:user_id>")
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
    
    user = User.query.get_or_404(user_id)
    user.status = 'rejected'
    db.session.commit()
    # In a real app, we would send an email here.
    flash(f'User {user.username} has been rejected.', 'warning')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/delete_user/<int:user_id>")
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/resolve_complaint/<int:complaint_id>")
@login_required
def resolve_complaint(complaint_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = 'Resolved'
    
    # Award credits to user
    user = User.query.get(complaint.user_id)
    user.credits += 10
    
    db.session.commit()
    flash(f'Complaint resolved. 10 Credits awarded to {user.username}.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/schedule_supply", methods=['POST'])
@login_required
def schedule_supply():
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    colony = request.form.get('colony')
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    action = request.form.get('action')
    notes = request.form.get('notes')
    
    date_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    
    new_schedule = Schedule(colony=colony, date_time=date_time, action=action, notes=notes)
    db.session.add(new_schedule)
    db.session.commit()
    flash('Water schedule updated successfully.', 'success')
    return redirect(url_for('admin.dashboard'))
