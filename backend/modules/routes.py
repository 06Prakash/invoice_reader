from .upload import register_upload_routes
from .template import register_template_routes
from .extract import register_extract_routes
from .serve import register_serve_routes

def register_routes(app):
    register_upload_routes(app)
    register_template_routes(app)
    register_extract_routes(app)
    register_serve_routes(app)
