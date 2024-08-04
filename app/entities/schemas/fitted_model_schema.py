from marshmallow import fields, post_load, Schema, validate
from app.entities.fitted_model import FittedModel
from entities.schemas.dump_mixin import DumpMixin


class FittedModelSchema(Schema, DumpMixin):
    _id = fields.Integer(dump_only=True)
    params = fields.Dict(allow_none=False)
    statistics = fields.Dict(allow_none=False)
    x = fields.List(
        fields.Float(), required=True, validate=validate.Length(min=1)
    )
    y = fields.List(
        fields.Float(), required=True, validate=validate.Length(min=1)
    )

    @post_load
    def make_investigation(self, data):
        return FittedModel(**data)


FITTED_MODEL_SCHEMA = FittedModelSchema()
