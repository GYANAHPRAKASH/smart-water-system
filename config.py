# pyre-ignore-all-errors
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Get URI from env, default to local if missing
    _mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/smart_water_db')
    
    # If using Atlas and the user forgot to specify the database name before the query string, inject it
    if 'mongodb.net/?' in _mongo_uri:
        _mongo_uri = _mongo_uri.replace('mongodb.net/?', 'mongodb.net/smart_water_db?')
    elif 'mongodb.net/' in _mongo_uri and not '?' in _mongo_uri and _mongo_uri.endswith('mongodb.net/'):
        _mongo_uri += 'smart_water_db'
        
    MONGO_URI = _mongo_uri

    # Flask-Mail (kept for backward compat but not used for sending)
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('AquaFlow', os.environ.get('MAIL_USERNAME') or 'noreply@aquaflow.com')

    # Brevo (formerly Sendinblue) — used for transactional emails via HTTPS
    # Works on Render free tier (no SMTP port restrictions)
    BREVO_API_KEY    = os.environ.get('BREVO_API_KEY')
    MAIL_SENDER_EMAIL = os.environ.get('MAIL_SENDER_EMAIL', 'vsgpvsjd2006@gmail.com')
