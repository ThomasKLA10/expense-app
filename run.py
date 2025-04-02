from app import create_app, db
from config import Config
import os

# Create app with appropriate configuration
app = create_app()

if __name__ == '__main__':
    # Only create tables when running directly (not when imported by WSGI server)
    with app.app_context():
        db.create_all()
    
    # Determine if we're in a production environment
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    # Only enable debug mode in development
    app.run(debug=not is_production)