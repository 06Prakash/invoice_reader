from flask import Blueprint
from .upload import register_upload_routes
from .extract import register_extract_routes
from .user_routes import user_bp
from .credit_routes import credit_routes
from .health_check import health_bp
from .razor_payment_routes import razor_bp
from .authentication_routes import auth_bp

def register_routes(app):
    """
    Register all application routes and blueprints.
    """
    # Register individual route modules
    register_upload_routes(app)
    register_extract_routes(app)

    # Register blueprints for users and credits
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(credit_routes, url_prefix='/credit')
    app.register_blueprint(razor_bp, url_prefix='/razor')
    app.register_blueprint(auth_bp, url_prefix='/auth')
