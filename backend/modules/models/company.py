from extensions import db

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, index=True)  # Add index for faster lookups
    name = db.Column(db.String(150), unique=True, nullable=False)
    credit_count = db.Column(db.Integer, default=0, nullable=False)  # Total credits for page extractions

    def __repr__(self):
        return f"<Company {self.name}, Credits: {self.credit_count}>"
