# backend/modules/routes.py
from .upload import register_upload_routes
from .template import register_template_routes
from .extract import register_extract_routes
from .user_routes import user_bp

def register_routes(app):
    register_upload_routes(app)
    register_template_routes(app)
    register_extract_routes(app)
    app.register_blueprint(user_bp, url_prefix='/user')
