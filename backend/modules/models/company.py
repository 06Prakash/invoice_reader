from extensions import db

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, index=True)  # Add index for faster lookups
    name = db.Column(db.String(150), unique=True, nullable=False)  # Organization name

    def __repr__(self):
        return f"<Company {self.name}>"
