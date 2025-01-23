from marshmallow import fields, post_load, Schema
from entities.schemas.dump_mixin import DumpMixin
from entities.adsorbate import Adsorbate


class AdsorbateSchema(Schema, DumpMixin):
    id = fields.Integer(missing=None)
    ion_name = fields.Str(required=True)
    iupac_name = fields.Str(required=True)
    formula = fields.Str(required=True)

    @post_load
    def make_model(self, data, **kwargs):
        return Adsorbate(**data)


ADSORBATE_SCHEMA = AdsorbateSchema()

