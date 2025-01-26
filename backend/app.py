# backend/app.py
import logging
import os
import importlib
import pkgutil
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate 
from extensions import db, bcrypt, login_manager, jwt, mail
from modules.routes import register_routes

def import_all_models(package_name):
    """
    Dynamically imports all modules in the specified package.
    This ensures all models are registered with Flask-Migrate.
    """
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if not is_pkg:
            importlib.import_module(module_name)

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    CORS(app)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.config.from_object('config')

    # In `create_app()` function, just call:
    import_all_models('modules.models')
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)  # Attach Flask-Migrate to the app and database

    # Register routes
    register_routes(app)

    # Static file serving for frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

