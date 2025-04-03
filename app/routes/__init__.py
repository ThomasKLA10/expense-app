from flask import Blueprint

# Create blueprints
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__)
receipt = Blueprint('receipt', __name__)
user = Blueprint('user', __name__)

# Import routes to register them with blueprints
from . import main_routes
from . import admin_routes
from . import receipt_routes
from . import user_routes
from . import ocr_routes

# Function to register all blueprints with the app
def register_blueprints(app):
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(receipt)
    app.register_blueprint(user)