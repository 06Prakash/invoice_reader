from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Float, DateTime, Text
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from extensions import db, bcrypt
from flask_login import UserMixin

class FileProcessing(db.Model):
    __tablename__ = "file_processing"

    id = Column(Integer, primary_key=True)
    extraction_attempt_id = Column(Integer, ForeignKey('extraction_attempt.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True)
    file_name = Column(String(255), nullable=False)
    status = Column(String(50), default="Pending")
    file_size_mb = Column(Numeric(precision=10, scale=2), nullable=True)
    total_pages = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    extraction_attempt = relationship('ExtractionAttempt', backref=backref('file_processes', lazy=True))
    user = relationship('User', backref=backref('file_processes', lazy=True))
    company = relationship('Company', backref=backref('file_processes', lazy=True))

    def mark_completed(self, processing_time):
        """Mark file processing as completed."""
        self.status = "Completed"
        self.processing_time = processing_time
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message):
        """Mark file as failed with an error message."""
        self.status = "Failed"
        self.error_message = error_message
