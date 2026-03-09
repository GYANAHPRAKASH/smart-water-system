# pyre-ignore-all-errors
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from . import mongo, login_manager

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except InvalidId:
        pass
    return None

# For Flask-Login to work with MongoDB, we need a custom User class
# Since there is no SQLAlchemy `db.Model` anymore, we just wrap a dictionary
class User(UserMixin):
    def __init__(self, user_dict):
        self.user_data = user_dict
        # UserMixin expects `id` to be a string
        self.id = str(user_dict.get('_id'))
        
    @property
    def username(self):
        return self.user_data.get('username')
        
    @property
    def role(self):
        return self.user_data.get('role', 'user')
        
    @property
    def status(self):
        return self.user_data.get('status', 'pending')
        
    @property
    def credits(self):
        return self.user_data.get('credits', 0)
        
    @property
    def first_name(self):
        return self.user_data.get('first_name')
        
    @property
    def last_name(self):
        return self.user_data.get('last_name')
        
    @property
    def phone(self):
        return self.user_data.get('phone')
        
    @property
    def door_no(self):
        return self.user_data.get('door_no')
        
    @property
    def colony(self):
        return self.user_data.get('colony')
        
    @property
    def password_hash(self):
        return self.user_data.get('password_hash')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @staticmethod
    def generate_hash(password):
        return generate_password_hash(password)

# No other classes are STRICTLY required because MongoDB is schema-less.
# We will just insert dictionaries into collections like `mongo.db.complaints`.
# However, you could define factory functions here if you wanted to strictly format dicts.
