from marshmallow import fields, post_load, Schema
from entities.linearization import Linearization
from .dump_mixin import DumpMixin


class LinearizationSchema(Schema, DumpMixin):
    linearization_id = fields.Integer(missing=None)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(required=True)
    parameters = fields.Dict(allow_none=False)
    model_id = fields.Integer()
    constants = fields.List( fields.Str, allow_none=True)

    @post_load
    def make_linearization(self, data, **kwargs):
        return Linearization(**data)


LINEARIZATION_SCHEMA = LinearizationSchema()
