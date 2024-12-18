import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create uploads directory
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Only allow HTTP in development
    if app.debug:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from .routes import main
    from .auth import auth as auth_blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app