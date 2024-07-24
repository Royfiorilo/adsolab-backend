from marshmallow import fields, post_load, Schema
from app.entities.no_linear_model import NoLinearModel
from app.entities.schemas.linearization_schema import LinearizationSchema


class ModelSchema(Schema):
    _id = fields.Integer(dump_only=True)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(required=True)
    parameters = fields.Dict(allow_none=False)
    linearizations = fields.List(fields.Nested(LinearizationSchema), missing=None)

    @post_load
    def make_model(self, data):
        return NoLinearModel(**data)


MODEL_SCHEMA = ModelSchema()


__all__ = ['LinearizationSchema']
