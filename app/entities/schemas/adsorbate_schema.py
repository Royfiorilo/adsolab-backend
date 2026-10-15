from marshmallow import fields, post_load, pre_load, Schema
from marshmallow.validate import Length
from entities.schemas.dump_mixin import DumpMixin
from entities.adsorbate import Adsorbate

# Column sizes of the adsorbate table.
MAX_ION_NAME = 100
MAX_IUPAC_NAME = 100
MAX_FORMULA = 10


def normalize_text(value):
    """Trims and collapses inner whitespace; anything that is not a string is left for validation."""
    return ' '.join(value.split()) if isinstance(value, str) else value


class AdsorbateSchema(Schema, DumpMixin):
    id = fields.Integer(missing=None)
    ion_name = fields.Str(required=True)
    iupac_name = fields.Str(required=True)
    formula = fields.Str(required=True)

    @post_load
    def make_model(self, data, **kwargs):
        return Adsorbate(**data)


ADSORBATE_SCHEMA = AdsorbateSchema()


class AdsorbateCreationSchema(Schema):
    """Payload of POST /adsorbates."""
    ion_name = fields.Str(required=True, validate=Length(min=1, max=MAX_ION_NAME))
    iupac_name = fields.Str(required=True, validate=Length(min=1, max=MAX_IUPAC_NAME))
    formula = fields.Str(required=True, validate=Length(min=1, max=MAX_FORMULA))

    @pre_load
    def normalize(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        return {key: normalize_text(value) for key, value in data.items()}


ADSORBATE_CREATION_SCHEMA = AdsorbateCreationSchema()

