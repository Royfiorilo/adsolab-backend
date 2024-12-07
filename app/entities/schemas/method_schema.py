from marshmallow import fields, post_load, Schema
from entities.schemas.dump_mixin import DumpMixin


class MethodSchema(Schema, DumpMixin):
    _id = fields.Integer(missing=None)
    name = fields.Str(required=True)
    code = fields.Str(required=True)
    description = fields.Str(required=True)


METHOD_SCHEMA = MethodSchema()

