from extensions import db
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Company {self.name}>"

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None

