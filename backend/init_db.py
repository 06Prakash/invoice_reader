# backend/init_db.py
from app import db, app
from modules.models import Company, User

with app.app_context():
    db.drop_all()
    db.create_all()
    metadata = db.MetaData(bind=db.engine)
    metadata.reflect()
    tables = metadata.tables.keys()
    print("Tables created:", tables)
