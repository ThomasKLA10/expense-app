import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class Config:
    """Application configuration
    
    Environment variables:
    - SECRET_KEY: Used for session security (required)
    - DATABASE_URL: Database connection string (required)
    - GOOGLE_CLIENT_ID: OAuth client ID (required for auth)
    - GOOGLE_CLIENT_SECRET: OAuth client secret (required for auth)
    - MAIL_SERVER: SMTP server (default: smtp.gmail.com)
    - MAIL_PORT: SMTP port (default: 587)
    - MAIL_USE_TLS: Use TLS for email (default: True)
    - MAIL_USERNAME: Email username (required for sending emails)
    - MAIL_PASSWORD: Email password (required for sending emails)
    - ALLOWED_EMAIL_DOMAINS: Comma-separated list of allowed email domains
    """
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
    
    # Email Settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-gmail@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-app-specific-password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'BB Receipt App <your-gmail@gmail.com>')
    
    # Add this to your Config class
    ALLOWED_EMAIL_DOMAINS = os.environ.get('ALLOWED_EMAIL_DOMAINS', '').split(',') if os.environ.get('ALLOWED_EMAIL_DOMAINS') else []
    
    @staticmethod
    def get_current_time():
        return datetime.utcnow() + timedelta(hours=1)  # German time is UTC+1
