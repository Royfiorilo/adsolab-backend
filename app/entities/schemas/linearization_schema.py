from marshmallow import fields, post_load, Schema, validate

from app.entities.linearization import Linearization


class LinearizationSchema(Schema):
    linearization_id = fields.Integer(dump_only=True)
    name = fields.Str(required=True)
    formula = fields.Str(required=True)
    description = fields.Str(required=True)
    parameters = fields.Dict(allow_none=False)
    model_id = fields.Integer()

    @post_load
    def make_Linearization(self, data):
        return Linearization(**data)


LINEARIZATION_SCHEMA = LinearizationSchema()