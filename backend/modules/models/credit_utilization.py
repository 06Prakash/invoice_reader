from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from extensions import db
from datetime import datetime

class CreditUtilization(db.Model):
    __tablename__ = "credit_utilization"

    id = db.Column(db.Integer, primary_key=True)
    extraction_attempt_id = db.Column(db.Integer, db.ForeignKey('extraction_attempt.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    credits_used = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    extraction_attempt = db.relationship('ExtractionAttempt', backref=db.backref('credit_usages', lazy=True))
    user = db.relationship('User', backref=db.backref('credit_usages', lazy=True))
    company = db.relationship('Company', backref=db.backref('credit_usages', lazy=True))
