import os
from flask import Flask, render_template
from .extensions import db, migrate, login_manager
from config import Config
from .utils.email import mail
from .utils.patches import apply_all_patches
from .swagger import swagger_ui_blueprint, register_swagger_routes, SWAGGER_URL
import logging
from pathlib import Path
from .utils.file_management import archive_processed_receipts, cleanup_temp_reports

# Apply patches to fix dependency warnings
apply_all_patches()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # CRITICAL: If we're testing, ALWAYS use SQLite in-memory
    if os.environ.get('FLASK_ENV') == 'testing' or app.config.get('TESTING', False):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("USING TEST DATABASE: sqlite:///:memory:")
    else:
        print(f"USING PRODUCTION DATABASE: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Create uploads directory with absolute path
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = uploads_dir
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize Flask-Mail
    mail.init_app(app)
    
    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    # Register routes from the routes package
    from .routes import register_blueprints
    register_blueprints(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Add CLI command for file management
    @app.cli.command("manage-files")
    def manage_files_command():
        """Archive receipts and clean up temporary files."""
        with app.app_context():
            archived = archive_processed_receipts()
            cleaned = cleanup_temp_reports()
            print(f"Archived {archived} receipts and cleaned up {cleaned} temporary files.")

    # Register Swagger UI blueprint
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    register_swagger_routes(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to response"""
        if not app.debug:  # Only in production
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    return app

def create_receipt(user_id, amount, currency, category, file_path=None, **kwargs):
    """Helper function to create a receipt with common fields"""
    from .models import Receipt
    receipt = Receipt(
        user_id=user_id,
        amount=amount,
        currency=currency,
        category=category,
        file_path_db=file_path,
        **kwargs
    )
    db.session.add(receipt)
    return receipt