from marshmallow import fields, post_load, Schema
from entities.no_linear_model import NoLinearModel
from entities.schemas.linearization_schema import LinearizationSchema
from entities.schemas.dump_mixin import DumpMixin


class ModelSchema(Schema, DumpMixin):
    _id = fields.Integer(missing=None)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(required=True)
    parameters = fields.Dict(allow_none=False)
    linearizations = fields.List(fields.Nested(LinearizationSchema), missing=None)
    constants = fields.List(fields.Str, allow_none=True)

    @post_load
    def make_model(self, data, **kwargs):
        return NoLinearModel(**data)


MODEL_SCHEMA = ModelSchema()


__all__ = ['LinearizationSchema']
