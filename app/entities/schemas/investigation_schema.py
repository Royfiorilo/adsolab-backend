from marshmallow import fields, post_load, Schema

from entities.investigation import InvestigationEntity
from .dump_mixin import DumpMixin


class InvestigationSchema(Schema, DumpMixin):
    investigation_id = fields.Integer(missing=None)
    sample_id = fields.Integer()

    @post_load
    def make_investigation(self, data, **kwargs):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()
