# backend/app.py
import logging
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate 
from extensions import db, bcrypt, login_manager, jwt
from modules.routes import register_routes

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    CORS(app)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.config.from_object('config')

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
