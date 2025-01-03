from extensions import db

class BusinessCredit(db.Model):
    __tablename__ = 'business_credit'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    credit_count = db.Column(db.Integer, nullable=False, default=0)

    company = db.relationship('Company', backref=db.backref('business_credits', lazy=True))

    def __repr__(self):
        return f"<BusinessCredit for {self.company.name}: {self.credit_count}>"
