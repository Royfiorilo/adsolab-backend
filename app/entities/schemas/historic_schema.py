from wsgiref import validate

from marshmallow import fields, Schema, post_load, EXCLUDE

from database import FittedModel
from entities.historic import Comparison, FittedModel, FittedMethod, Version
from entities.schemas.dump_mixin import DumpMixin


class FittedMethodSchema(Schema, DumpMixin):
    class Meta:
        unknown = EXCLUDE
    name = fields.Str(allow_none=False)
    params = fields.List( fields.Dict, allow_none=False, data_key="parameters")
    statistics = fields.Dict(allow_none=False)
    residuals = fields.Dict(allow_none=False)

    @post_load
    def make_fitted_method(self, data, **kwargs):
        return FittedMethod(**data)


class ComparisonSchema(Schema, DumpMixin):
    comparison_id = fields.Integer(dump_only=True)
    heuristic = fields.Dict(allow_none=False)
    ml = fields.Dict(allow_none=False, data_key='ridge')

    @post_load
    def make_comparison(self, data, **kwargs):
        return Comparison(**data)


class FittedModelSchema(Schema, DumpMixin):
    model_id = fields.Integer(allow_none=False, data_key='model')
    best_adjust = fields.Str(allow_none=False)
    adjustment_methods = fields.List(
        fields.Nested(FittedMethodSchema), required=True
    )

    @post_load
    def make_model(self, data, **kwargs):
        return FittedModel(**data)


class VersionSchema(Schema, DumpMixin):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer(dump_only=True)
    investigation_id = fields.Integer()
    iterations = fields.Integer()
    steps = fields.Integer()
    created_at = fields.DateTime()
    seeds = fields.List(fields.Dict, allow_none=False)
    fitted_models = fields.List(fields.Nested(FittedModelSchema), allow_none=False, data_key='results')
    comparison = fields.Nested(ComparisonSchema, allow_none=False)

    @post_load
    def make_version(self, data, **kwargs):
        return Version(**data)



FITTED_METHOD_SCHEMA = FittedMethodSchema()
COMPARISON_SCHEMA = ComparisonSchema()
FITTED_MODEL_SCHEMA = FittedModelSchema()
VERSION_SCHEMA = VersionSchema()

__all__ = ["FittedMethodSchema", "ComparisonSchema"]
