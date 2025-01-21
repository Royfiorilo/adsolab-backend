from marshmallow import fields, post_load, Schema
from entities.schemas.dump_mixin import DumpMixin
from entities.adsorbent import Adsorbent

class AdsorbentSchema(Schema, DumpMixin):
    id = fields.Integer(missing=None)
    name = fields.Str(required=True)

    @post_load
    def make_model(self, data, **kwargs):
        return Adsorbent(**data)

ADSORBENT_SCHEMA = AdsorbentSchema()

