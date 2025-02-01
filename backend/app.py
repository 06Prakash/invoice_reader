import logging
import os
import importlib
import pkgutil
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from extensions import db, bcrypt, login_manager, jwt, mail
from modules.routes import register_routes
from modules.logging_util import setup_logger, cleanup_old_logs
from dotenv import load_dotenv
from celery import Celery

# Load environment variables from .env
load_dotenv()

def import_all_models(package_name):
    """
    Dynamically imports all modules in the specified package.
    This ensures all models are registered with Flask-Migrate.
    """
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if not is_pkg:
            importlib.import_module(module_name)

def make_celery(app):
    """
    Configure Celery to work with Flask.
    """
    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
        backend=app.config.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    )
    celery.conf.update(app.config)
    
    # Push Flask context for Celery workers
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app():
    """
    Initialize the Flask application with required configurations and extensions.
    """
    app = Flask(__name__, static_folder="static", static_url_path="")
    CORS(app)

    # Configure logging
    logger = setup_logger(__name__)

    # Load configuration based on FLASK_ENV
    flask_env = os.getenv("FLASK_ENV", "production")
    app.config.from_object("config")

    if flask_env == "development":
        app.config["DEBUG"] = True
        app.config["CELERY_BROKER_URL"] = "redis://redis:6379/0"
        app.config["CELERY_RESULT_BACKEND"] = "redis://redis:6379/0"
    else:
        app.config["DEBUG"] = False
        app.config["CELERY_BROKER_URL"] = os.getenv("AZURE_STORAGE_QUEUE_URL")
        app.config["CELERY_RESULT_BACKEND"] = None  # No result backend needed for Azure

    logger.info(f"Starting Flask App in {flask_env} mode...")

    # Register models & extensions
    import_all_models("modules.models")
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Initialize Flask-Migrate
    Migrate(app, db)

    # Initialize Celery with Flask
    global celery_app
    celery_app = make_celery(app)

    # Register routes
    register_routes(app)

    # Static file serving for frontend (React)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + "/" + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, "index.html")

    return app

app = create_app()

if __name__ == "__main__":
    cleanup_old_logs()
    
    # Set port dynamically
    port = 5000 if os.getenv("FLASK_ENV", "development") == "development" else 80

    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
