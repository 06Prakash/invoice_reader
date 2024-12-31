from extensions import db

class Credit(db.Model):
    __tablename__ = 'credit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Personal credits
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # Organization credits
    credit_count = db.Column(db.Integer, nullable=False, default=0)  # Available credits

    user = db.relationship('User', backref=db.backref('credits', lazy=True))
    company = db.relationship('Company', backref=db.backref('credits', lazy=True))

    def __repr__(self):
        entity = self.user.username if self.user else self.company.name
        return f"<Credit for {entity}: {self.credit_count}>"
