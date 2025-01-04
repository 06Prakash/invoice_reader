from extensions import db

class BusinessCredit(db.Model):
    __tablename__ = 'business_credit'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    # Update credit_count to db.Numeric with precision and scale
    credit_count = db.Column(db.Numeric(precision=10, scale=2), nullable=False, default=0.00)

    company = db.relationship('Company', backref=db.backref('business_credits', lazy=True))

    def __repr__(self):
        return f"<BusinessCredit for {self.company.name}: {self.credit_count}>"
