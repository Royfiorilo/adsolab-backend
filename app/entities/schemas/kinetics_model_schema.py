from marshmallow import fields, Schema, post_load

from entities.kinetics_model import KineticsModelEntity, KineticsLinearizationEntity
from entities.schemas.dump_mixin import DumpMixin


class KineticsLinearizationSchema(Schema, DumpMixin):
    linearization_id = fields.Integer(load_default=None)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(load_default=None)
    parameters = fields.Dict(allow_none=True)
    constants = fields.List(fields.Str(), allow_none=True)
    kinetic_model_id = fields.Integer(load_default=None)
    latex_formula = fields.Str(load_default=None)

    @post_load
    def make_linearization(self, data, **kwargs):
        return KineticsLinearizationEntity(**data)


class KineticsModelSchema(Schema, DumpMixin):
    _id = fields.Integer(load_default=None)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(required=True)
    parameters = fields.Dict(allow_none=False)
    constants = fields.List(fields.Str(), allow_none=True)
    latex_formula = fields.Str(required=True)
    linearizations = fields.List(fields.Nested(KineticsLinearizationSchema), load_default=None)

    @post_load
    def make_model(self, data, **kwargs):
        return KineticsModelEntity(**data)


KINETICS_MODEL_SCHEMA = KineticsModelSchema()
KINETICS_LINEARIZATION_SCHEMA = KineticsLinearizationSchema()
