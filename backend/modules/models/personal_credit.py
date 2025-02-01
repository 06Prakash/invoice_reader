from extensions import db

class PersonalCredit(db.Model):
    __tablename__ = 'personal_credit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Update credit_count to db.Numeric with precision and scale
    credit_count = db.Column(db.Numeric(precision=10, scale=2), nullable=False, default=0.00)

    user = db.relationship('User', backref=db.backref('personal_credit', uselist=False))

    def __repr__(self):
        return f"<PersonalCredit for {self.user.username}: {self.credit_count}>"
