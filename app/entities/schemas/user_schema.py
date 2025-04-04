from marshmallow import Schema, fields

from entities.schemas.dump_mixin import DumpMixin


class UserSchema(Schema, DumpMixin):
    id = fields.Integer()
    email = fields.Str()
