from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from . import mongo
from .models import User
from datetime import datetime
from bson.objectid import ObjectId
from .ai_module import analyze_complaint, generate_simulated_data, predict_demand, detect_anomalies

admin = Blueprint('admin', __name__)

@admin.route("/admin/dashboard")
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access Denied: You are not an admin.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Get selected colony from query params, default to first one
    selected_colony = request.args.get('colony', 'Anna Nagar')
    all_colonies = ["Anna Nagar", "Nungambakkam", "T. Nagar", "Alwarpet", "Gopalapuram"]
    
    # AI Analysis & Data for Selected Colony (Dashboard Overview)
    predicted_demand = predict_demand(selected_colony)
    anomalies = detect_anomalies(selected_colony)
    
    # User Management Filter
    user_filter_colony = request.args.get('user_colony', 'All')
    user_query = {}
    if user_filter_colony != 'All':
        user_query['colony'] = user_filter_colony
        
    # Users
    users_data = list(mongo.db.users.find(user_query))
    users = [User(u) for u in users_data]
    
    # Leaderboard Logic: Get Top 2 globally (or optionally filtered)
    # Let's get global top 2 regardless of filter to always show city-wide leaders
    top_users_data = list(mongo.db.users.find({'role': 'user'}).sort('credits', -1).limit(2))
    # We just need their IDs to tag them in the UI
    top_user_ids = [str(u['_id']) for u in top_users_data if u.get('credits', 0) > 0]
    
    # Pending Users (Applying same filter if desired, or keep showing all. Let's apply filter for consistency)
    pending_query = {'status': 'pending'}
    if user_filter_colony != 'All':
        pending_query['colony'] = user_filter_colony
        
    pending_users_data = mongo.db.users.find(pending_query)
    pending_users = [User(u) for u in pending_users_data]
    
    # Complaints
    # MongoDB sort by created_at DESC: -1
    raw_complaints = list(mongo.db.complaints.find().sort('created_at', -1))
    complaints = []
    active_complaints_count = 0
    for c in raw_complaints:
        # Resolve user
        u_data = mongo.db.users.find_one({'_id': c['user_id']})
        if u_data:
            c['user'] = {'username': u_data.get('username'), 'colony': u_data.get('colony')}
        else:
            c['user'] = {'username': 'Unknown', 'colony': 'Unknown'}
        # Jinja uses c.id, we can provide c['id'] because Jinja handles dict keys like attributes
        c['id'] = str(c['_id'])
        if c.get('status') != 'Resolved':
            active_complaints_count = active_complaints_count + 1
        complaints.append(c)
    
    # Schedules
    raw_schedules = list(mongo.db.schedules.find({'colony': selected_colony}).sort('date_time', -1))
    
    schedules_data = [{
        'id': str(s['_id']),
        'colony': s['colony'],
         'action': s['action'],
         'notes': s.get('notes', ''),
         'date_time': s['date_time'].isoformat(),
         'time_str': s['date_time'].strftime("%I:%M %p")
    } for s in raw_schedules]
    
    # ---------------- MAP DATA PREPARATION ----------------
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
    
    colony_coords = {
        "Anna Nagar": [13.0850, 80.2101],
        "Nungambakkam": [13.0630, 80.2433],
        "T. Nagar": [13.0405, 80.2337],
        "Alwarpet": [13.0335, 80.2536],
        "Gopalapuram": [13.0475, 80.2584]
    }
    
    map_data = []
    for col in all_colonies:
        # Check Today's Schedule
        today_sched = list(mongo.db.schedules.find({
            'colony': col,
            'date_time': {'$gte': today_start, '$lte': today_end}
        }))
        
        status = 'Normal' # Default
        if any(s['action'] == 'Shutdown' for s in today_sched):
            status = 'Shutdown'
        elif any(s['action'] == 'Supply' for s in today_sched):
            status = 'Supply'
            
        # Check active High Priority Complaints
        active_complaints = list(mongo.db.complaints.find({
            'status': {'$ne': 'Resolved'},
            'priority': 'High'
        }))
        
        # Filter active complaints by determining user colony
        critical_issues = 0
        for c in active_complaints:
            u_data = mongo.db.users.find_one({'_id': c['user_id']})
            if u_data and u_data.get('colony') == col:
                critical_issues = critical_issues + 1
                
        map_data.append({
            'colony': col,
            'coords': colony_coords.get(col, [13.0827, 80.2707]),
            'status': status,
            'critical_issues': critical_issues
        })
    # ----------------------------------------------------

    return render_template('admin_dashboard.html', 
                           users=users, 
                           pending_users=pending_users, 
                           complaints=complaints, 
                           active_complaints_count=active_complaints_count,
                           schedules=raw_schedules, # Not strictly needed if admin_calendar uses JSON, but keeping for template structure
                           schedules_data=schedules_data,
                           predictions=predicted_demand,
                           anomalies=anomalies,
                           selected_colony=selected_colony,
                           user_filter_colony=user_filter_colony,
                           all_colonies=all_colonies,
                           map_data=map_data,
                           top_user_ids=top_user_ids)

@admin.route("/admin/approve_user/<user_id>")
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
    
    mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'approved'}})
    flash('User has been approved.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/reject_user/<user_id>")
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
    
    mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'rejected'}})
    flash('User has been rejected.', 'warning')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/delete_user/<user_id>")
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash('User has been deleted.', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/resolve_complaint/<complaint_id>")
@login_required
def resolve_complaint(complaint_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    complaint = mongo.db.complaints.find_one({'_id': ObjectId(complaint_id)})
    if complaint:
        mongo.db.complaints.update_one({'_id': ObjectId(complaint_id)}, {'$set': {'status': 'Resolved'}})
        
        # Award credits
        user_id = complaint.get('user_id')
        if user_id:
            mongo.db.users.update_one({'_id': user_id}, {'$inc': {'credits': 10}})
        
        # Find username for flash
        user = mongo.db.users.find_one({'_id': user_id})
        uname = user.get('username') if user else 'User'
        flash(f'Complaint resolved. 10 Credits awarded to {uname}.', 'success')
        
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
    
    # Override logic: If action is Shutdown, clear any Supply for this day/colony
    if action == 'Shutdown':
        start_of_day = date_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date_time.replace(hour=23, minute=59, second=59, microsecond=999)
        mongo.db.schedules.delete_many({
            'colony': colony,
            'action': 'Supply',
            'date_time': {'$gte': start_of_day, '$lte': end_of_day}
        })
    
    new_schedule = {
        'colony': colony,
        'date_time': date_time,
        'action': action,
        'notes': notes
    }
    mongo.db.schedules.insert_one(new_schedule)
    flash('Water schedule updated successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route("/admin/delete_schedule/<schedule_id>")
@login_required
def delete_schedule(schedule_id):
    if current_user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    mongo.db.schedules.delete_one({'_id': ObjectId(schedule_id)})
    flash('Schedule deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))
