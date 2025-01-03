from extensions import db

class PersonalCredit(db.Model):
    __tablename__ = 'personal_credit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    credit_count = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship('User', backref=db.backref('personal_credit', uselist=False))

    def __repr__(self):
        return f"<PersonalCredit for {self.user.username}: {self.credit_count}>"
