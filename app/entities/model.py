from app import db

class Model (db.Model):
    __tablename__ = 'models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)