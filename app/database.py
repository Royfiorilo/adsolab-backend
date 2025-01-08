from app import db
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from entities.schemas.dump_mixin import DumpMixin


class Model(DumpMixin, db.Model):
    __tablename__ = 'model'

    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    linearizations = db.relationship('Linearization', backref='model', lazy=True)

class FittedModel(DumpMixin, db.Model):
    __tablename__ = 'fitted_model'

    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    x = db.Column(ARRAY(db.Float), nullable=False)
    y = db.Column(ARRAY(db.Float), nullable=False)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.investigation_id'), nullable=False)


class Sample(DumpMixin, db.Model):
    __tablename__ = 'sample'

    sample_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ce = db.Column(ARRAY(db.Float), nullable=False)
    qe = db.Column(ARRAY(db.Float), nullable=False)
    investigations = db.relationship('Investigation', backref='sample', lazy=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    temperature = db.Column(db.Float)
    measure_unit = db.Column(db.String(10))
    adsorbate_id = db.Column(db.Integer, db.ForeignKey('adsorbate.id'), nullable=False)
    adsorbent_id = db.Column(db.Integer, db.ForeignKey('adsorbent.id'), nullable=False)


class Investigation(DumpMixin, db.Model):
    __tablename__ = 'investigation'

    investigation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.sample_id'), nullable=False)
    #fitted_model = db.relationship('FittedModel', backref='investigation', lazy=True)


class Linearization(DumpMixin, db.Model):
    __tablename__ = 'linearization'

    linearization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model._id'), nullable=False)

class Method(DumpMixin, db.Model):
    __tablename__ = 'method'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    color = db.Column(db.String(10), nullable=False)

class Adsorbent(DumpMixin, db.Model):
    __tablename__ = 'adsorbent'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

class Adsorbate(DumpMixin, db.Model):
    __tablename__ = 'adsorbate'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ion_name = db.Column(db.String(100), nullable=False)
    IUPAC_name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(10), nullable=False)