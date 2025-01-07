from datetime import datetime
from extensions import db, bcrypt
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # Roles like 'admin', 'manager', etc.
    special_admin = db.Column(db.Boolean, default=False)  # For special administrators
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete flag
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete timestamp

    # OTP fields
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0, nullable=False)

    company = db.relationship('Company', backref=db.backref('users', lazy=True))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def soft_delete(self):
        """Mark the user as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted user."""
        self.is_deleted = False
        self.deleted_at = None
