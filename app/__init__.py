from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Import Blueprints
    from .routes_auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .routes_user import user as user_blueprint
    app.register_blueprint(user_blueprint)
    
    from .routes_admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    return app
