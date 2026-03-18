# pyre-ignore-all-errors
from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from config import Config

mongo        = PyMongo()
login_manager = LoginManager()
mail         = Mail()
oauth        = OAuth()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    # Register Google OAuth provider
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    from .routes_auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes_user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from .routes_admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .routes_api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
