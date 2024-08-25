from marshmallow import fields, post_load, Schema
from entities.investigation import InvestigationEntity
from entities.schemas.fitted_model_schema import FittedModelSchema
from .dump_mixin import DumpMixin

class InvestigationSchema(Schema, DumpMixin):
    investigation_id = fields.Integer(dump_only=True)
    sample_id = fields.Integer()
    #fitted_models = fields.Nested("FittedModelSchema")

    @post_load
    def make_investigation(self, data):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()
