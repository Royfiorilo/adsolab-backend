from datetime import datetime

from flask_security.models import fsqla
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY, JSON

from entities.schemas.dump_mixin import DumpMixin

db = SQLAlchemy()
fsqla.FsModels.set_db_info(db)


class Model(DumpMixin, db.Model):
    __tablename__ = 'model'

    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    constants = db.Column(ARRAY(db.String(5)), nullable=True)
    linearizations = db.relationship('Linearization', backref='model', lazy=True)
    latex_formula = db.Column(db.String(255), nullable=False)


class FittedModel(DumpMixin, db.Model):
    __tablename__ = 'fitted_model'

    fitted_model_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, nullable=False)
    best_adjust = db.Column(db.String(100), nullable=False)
    adjustment_methods = db.Column(ARRAY(db.JSON), nullable=False)
    version_id = db.Column(db.Integer, nullable=False)
    investigation_id = db.Column(db.Integer, nullable=False)
    seeds = db.Column(ARRAY(db.JSON), nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['version_id', 'investigation_id'],
            ['version.version_id', 'version.investigation_id'],
            ondelete="CASCADE"
        ),
    )


class Comparison(DumpMixin, db.Model):
    __tablename__ = 'comparison'

    comparison_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    heuristic = db.Column(db.JSON, nullable=False)
    ml = db.Column(db.JSON, nullable=False)
    version_id = db.Column(db.Integer, nullable=False, unique=True)
    investigation_id = db.Column(db.Integer, nullable=False, unique=True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['version_id', 'investigation_id'],
            ['version.version_id', 'version.investigation_id'],
            ondelete="CASCADE"
        ),
    )


class Version(DumpMixin, db.Model):
    __tablename__ = 'version'

    version_id = db.Column(db.Integer, primary_key=True)
    iterations = db.Column(db.Integer, nullable=True)
    steps = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.investigation_id'), primary_key=True)
    fitted_models = db.relationship('FittedModel', backref='version', cascade="all, delete-orphan", lazy=True)
    comparison = db.relationship('Comparison', backref='version', cascade="all, delete-orphan", lazy=True,
                                 uselist=False)


class Sample(DumpMixin, db.Model):
    __tablename__ = 'sample'

    sample_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ce = db.Column(ARRAY(db.Float), nullable=False)
    qe = db.Column(ARRAY(db.Float), nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    temperature = db.Column(db.Float)
    measure_unit = db.Column(db.String(10))
    adsorbate_id = db.Column(db.Integer, db.ForeignKey('adsorbate.id'), nullable=False)
    adsorbent_id = db.Column(db.Integer, db.ForeignKey('adsorbent.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Investigation(DumpMixin, db.Model):
    __tablename__ = 'investigation'

    investigation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.sample_id'), nullable=False)
    sample = db.relationship('Sample', backref='investigation', uselist=False, lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='investigation', uselist=False, lazy=True)


class Linearization(DumpMixin, db.Model):
    __tablename__ = 'linearization'

    linearization_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    parameters = db.Column(JSON, nullable=False)
    constants = db.Column(ARRAY(db.String(5)), nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model._id'), nullable=False)
    latex_formula = db.Column(db.String(255), nullable=False)


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
    iupac_name = db.Column(db.String(100), nullable=False)
    formula = db.Column(db.String(10), nullable=False)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    deleted_at = db.Column(db.DateTime, nullable=True)
    pass
