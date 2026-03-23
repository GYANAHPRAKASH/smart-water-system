# pyre-ignore-all-errors
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

mongo         = PyMongo()
login_manager = LoginManager()
mail          = Mail()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Trust the reverse proxy from Render so URLs are generated as https://
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from .routes_auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes_user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from .routes_admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .routes_api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
