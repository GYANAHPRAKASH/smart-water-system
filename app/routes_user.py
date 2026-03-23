# pyre-ignore-all-errors
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from . import mongo
from bson.objectid import ObjectId
from .ai_module import analyze_complaint, predict_demand
from datetime import datetime

user = Blueprint('user', __name__)

@user.route("/user/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
        
    my_complaints = list(mongo.db.complaints.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1))
    
    # Filter schedules for the user's colony
    schedules = list(mongo.db.schedules.find({'colony': current_user.colony}).sort('date_time', -1))
    
    # Serialize schedules for JS calendar
    schedules_data = [{
        'colony': s['colony'],
         'action': s['action'],
         'notes': s.get('notes', ''),
         'date_time': s['date_time'].isoformat(),
         'time_str': s['date_time'].strftime("%I:%M %p")
    } for s in schedules]
    
    # Check if user is top 2 (Gamification constraint)
    top_users_data = list(mongo.db.users.find({'role': 'user'}).sort('credits', -1).limit(2))
    top_user_ids = [str(u['_id']) for u in top_users_data if u.get('credits', 0) > 0]
    is_top_user = str(current_user.id) in top_user_ids

    # AI: 7-day demand predictions for the user's own colony
    predictions = predict_demand(current_user.colony) if current_user.colony else []

    return render_template('user_dashboard.html', 
                           complaints=my_complaints, 
                           schedules=schedules, 
                           schedules_data=schedules_data,
                           is_top_user=is_top_user,
                           predictions=predictions)

@user.route("/user/submit_complaint", methods=['POST'])
@login_required
def submit_complaint():
    complaint_type = request.form.get('type')
    description = request.form.get('description')
    
    # AI Logic
    priority = analyze_complaint(description)
    
    new_complaint = {
        'user_id': ObjectId(current_user.id),
        'type': complaint_type,
        'description': description,
        'priority': priority,
        'status': 'Pending',
        'created_at': datetime.utcnow()
    }
    mongo.db.complaints.insert_one(new_complaint)
    
    flash(f'Complaint Submitted. Priority set to {priority} based on analysis.', 'success')
    return redirect(url_for('user.dashboard'))
