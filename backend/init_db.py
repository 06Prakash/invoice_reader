# backend/init_db.py
from extensions import db
from flask import Flask
from backend.modules.models.company import Company
from backend.modules.models.user import User

# Minimal Flask app context for database initialization
app = Flask(__name__)
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI='postgresql://myuser:mypassword@db:5432/mydatabase',
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