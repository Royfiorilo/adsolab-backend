from marshmallow import fields, post_load, Schema, validate
from entities.fitted_model import FittedModel
from .dump_mixin import DumpMixin


class FittedModelSchema(Schema, DumpMixin):
    fitted_model_id = fields.Integer(dump_only=True)
    investigation_id = fields.Integer(required=True)
    #step = fields.Integer()
    #iteration = fields.Integer()
    #parameters = fields.Dict(allow_none=False)
    #statistics = fields.Dict(allow_none=False)
    #ml_comparison_result = fields.Dict(allow_none=False)
    #heuristic_result = fields.Dict(allow_none=False)
    #seed = fields.Dict(allow_none=False)
    models = fields.List(fields.Integer(), allow_none=False)
    #seed_generation_mode = fields.String(allow_none=False)
    #creation_date = fields.DateTime(dump_only=True)
    #version = fields.Integer()


    @post_load
    def make_fitted_model(self, data, **kwargs):
        return FittedModel(**data)


FITTED_MODEL_SCHEMA = FittedModelSchema()
