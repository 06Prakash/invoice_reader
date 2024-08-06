import os

UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'resources/json_templates'
ALLOWED_EXTENSIONS = {'pdf'}

SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///site.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_jwt_secret_key')
SQLALCHEMY_POOL_SIZE = 20  # Increase pool size
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_POOL_TIMEOUT = 30

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(TEMPLATE_FOLDER):
    os.makedirs(TEMPLATE_FOLDER)
