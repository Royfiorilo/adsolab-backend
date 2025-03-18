from marshmallow import fields, post_load, Schema

from entities.investigation import InvestigationEntity
from .sample_schema import SampleSchema, DumpMixin



class InvestigationSchema(Schema, DumpMixin):
    investigation_id = fields.Integer(missing=None)
    sample_id = fields.Integer()
    sample = fields.Nested(SampleSchema)
    user_id = fields.Integer()
    
    
    @post_load
    def make_investigation(self, data, **kwargs):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()
