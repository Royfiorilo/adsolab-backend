from marshmallow import fields, post_load, Schema

from entities.investigation import InvestigationEntity
from .dump_mixin import DumpMixin
from .sample_schema import SampleSchema



class InvestigationSchema(Schema, DumpMixin):
    investigation_id = fields.Integer(missing=None)
    sample_id = fields.Integer()
    sample = fields.Nested(SampleSchema)
    
    
    @post_load
    def make_investigation(self, data, **kwargs):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()
