import pytest
import os
from app import create_app, db

@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    # Force test configuration
    os.environ['FLASK_ENV'] = 'testing'
    
    # Create the app with test config
    app = create_app()
    
    # CRITICAL: Override the database URI to use SQLite in-memory
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # This is crucial
        'WTF_CSRF_ENABLED': False,
    })
    
    # Create the database and tables for testing only
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for a test."""
    with app.app_context():
        yield db.session 