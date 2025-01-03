from extensions import db
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, index=True)  # Add index for faster lookups
    name = db.Column(db.String(150), unique=True, nullable=False)  # Organization name
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete flag
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete timestamp

    def __repr__(self):
        return f"<Company {self.name}>"

    def soft_delete(self):
        """Mark the company as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted company."""
        self.is_deleted = False
        self.deleted_at = None
