from marshmallow import fields, post_load, Schema
from entities.investigation import InvestigationEntity
from entities.schemas.fitted_model_schema import FittedModelSchema
from .dump_mixin import DumpMixin

class InvestigationSchema(Schema, DumpMixin):
    investigation_id = fields.Integer(missing=None)
    #TODO: Analizar si no es necesario resolver acá la sample en vez del id únicamente.
    sample_id = fields.Integer()
    #fitted_models = fields.Nested("FittedModelSchema")

    @post_load
    def make_investigation(self, data, **kwargs):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()
