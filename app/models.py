from datetime import datetime
from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user') # 'admin' or 'user'
    status = db.Column(db.String(10), nullable=False, default='pending') # 'pending', 'approved', 'rejected'
    credits = db.Column(db.Integer, default=0)
    
    # User Details
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    door_no = db.Column(db.String(20), nullable=False)
    colony = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}', '{self.status}')"

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True) # Optional description
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Resolved
    priority = db.Column(db.String(10), nullable=False, default='Medium') # High, Medium, Low
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('complaints', lazy=True))

    def __repr__(self):
        return f"Complaint('{self.type}', '{self.status}', '{self.priority}')"

class WaterUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colony = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount_liters = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"WaterUsage('{self.colony}', '{self.date}', '{self.amount_liters}')"

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colony = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    action = db.Column(db.String(20), nullable=False) # Supply, Shutdown
    notes = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Schedule('{self.colony}', '{self.date_time}', '{self.action}')"

class AIRequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(50), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    output_data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"AIRequestLog('{self.endpoint}', '{self.timestamp}')"
