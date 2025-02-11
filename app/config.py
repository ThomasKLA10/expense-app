import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/uploads'
    SESSION_COOKIE_DOMAIN = None
    
    # Google OAuth credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Email Settings for testing with Gmail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-gmail@gmail.com'
    MAIL_PASSWORD = 'your-app-specific-password'  # Use App Password from Google Account
    MAIL_DEFAULT_SENDER = ('BB Receipt App', 'your-gmail@gmail.com')
    
    @staticmethod
    def get_current_time():
        return datetime.utcnow() + timedelta(hours=1)  # German time is UTC+1
