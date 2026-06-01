from marshmallow import fields, Schema, post_load

from entities.schemas.dump_mixin import DumpMixin
from entities.schemas.kinetics_sample_schema import KineticsSampleSchema
from entities.schemas.user_schema import UserSchema


class KineticsInvestigationSchema(Schema, DumpMixin):
    kinetic_investigation_id = fields.Integer(load_default=None)
    kinetic_sample_id = fields.Integer()
    sample = fields.Nested(KineticsSampleSchema, load_default=None)
    user_id = fields.Integer(load_default=None)
    user = fields.Nested(UserSchema, load_default=None)


KINETICS_INVESTIGATION_SCHEMA = KineticsInvestigationSchema()
