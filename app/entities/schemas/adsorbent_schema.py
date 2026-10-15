from marshmallow import fields, post_load, pre_load, Schema
from marshmallow.validate import Length
from entities.schemas.adsorbate_schema import normalize_text
from entities.schemas.dump_mixin import DumpMixin
from entities.adsorbent import Adsorbent

# Column size of the adsorbent table.
MAX_NAME = 255

class AdsorbentSchema(Schema, DumpMixin):
    id = fields.Integer(missing=None)
    name = fields.Str(required=True)

    @post_load
    def make_model(self, data, **kwargs):
        return Adsorbent(**data)

ADSORBENT_SCHEMA = AdsorbentSchema()


class AdsorbentCreationSchema(Schema):
    """Payload of POST /adsorbents."""
    name = fields.Str(required=True, validate=Length(min=1, max=MAX_NAME))

    @pre_load
    def normalize(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        return {key: normalize_text(value) for key, value in data.items()}


ADSORBENT_CREATION_SCHEMA = AdsorbentCreationSchema()

