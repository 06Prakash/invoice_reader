from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from extensions import db
from datetime import datetime

class ExtractionAttempt(db.Model):
    __tablename__ = "extraction_attempt"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True)
    attempt_number = Column(Integer, nullable=False)
    total_files = Column(Integer, nullable=False, default=0)
    successful_files = Column(Integer, nullable=False, default=0)
    failed_files = Column(Integer, nullable=False, default=0)
    total_credits_used = Column(Numeric(precision=10, scale=2), nullable=False, default=0.00)
    status = Column(String(50), default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship('User', backref=backref('extraction_attempts', lazy=True))
    company = relationship('Company', backref=backref('extraction_attempts', lazy=True))

    def mark_completed(self, successful_files, failed_files, credits_used):
        """Mark attempt as completed and update stats."""
        self.status = "Completed"
        self.successful_files = successful_files
        self.failed_files = failed_files
        self.total_credits_used = credits_used
        self.completed_at = datetime.utcnow()
