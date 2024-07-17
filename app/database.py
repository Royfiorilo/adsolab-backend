from . import db
from sqlalchemy.dialects.postgresql import ARRAY, JSON


class Model(db.Model):
    __tablename__ = 'model'

    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    linearizations = db.relationship('Linearization', backref='model', lazy=True)

class FittedModel(db.Model):
    __tablename__ = 'fitted_model'

    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    x = db.Column(ARRAY(db.Integer), nullable=False)
    y = db.Column(ARRAY(db.Integer), nullable=False)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.investigation_id'), nullable=False)


class Sample(db.Model):
    __tablename__ = 'sample'

    sample_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ce = db.Column(ARRAY(db.Integer), nullable=False)
    qe = db.Column(ARRAY(db.Integer), nullable=False)
    investigations = db.relationship('Investigation', backref='sample', lazy=True)


class Investigation(db.Model):
    __tablename__ = 'investigation'
    investigation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.sample_id'), nullable=False)
    #fitted_model = db.relationship('FittedModel', backref='investigation', lazy=True)


class Linearization(db.Model):
    __tablename__ = 'linearization'
    linearization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model._id'), nullable=False)