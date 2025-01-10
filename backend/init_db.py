# backend/init_db.py
from extensions import db
from flask import Flask
from backend.modules.models.company import Company
from backend.modules.models.user import User
import os

# Fetch environment variables for database configuration
POSTGRES_USER = os.getenv('POSTGRES_USER', 'default_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'default_password')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'default_db')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')

# Minimal Flask app context for database initialization
app = Flask(__name__)
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app)

with app.app_context():
    # db.drop_all()  # Uncomment if needed
    db.create_all()
    metadata = db.MetaData(bind=db.engine)
    metadata.reflect()
    tables = metadata.tables.keys()
    print("Tables created:", tables)