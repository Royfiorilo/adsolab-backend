from marshmallow import fields, Schema, post_load, EXCLUDE, post_dump

from entities.historic import Comparison, FittedModel, FittedMethod, Version
from entities.schemas.dump_mixin import DumpMixin


class FittedMethodSchema(Schema, DumpMixin):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(allow_none=False)
    params = fields.List(
        fields.Dict,
        allow_none=False
    )
    parameters = fields.List(fields.Dict)
    statistics = fields.Dict(allow_none=False)
    residuals = fields.Dict(allow_none=False)

    def get_attribute(self, obj, attr, default):
        if attr == 'params' and hasattr(obj, 'parameters'):
            return getattr(obj, 'parameters')
        return super().get_attribute(obj, attr, default)

    @post_dump
    def handle_serialization(self, data, **kwargs):
        if 'params' in data:
            data['parameters'] = data.pop('params')
        return data

    @post_load
    def make_fitted_method(self, data, **kwargs):
        # Si tenemos 'parameters' en los datos, lo movemos a 'params'
        if 'parameters' in data:
            data['params'] = data.pop('parameters')
        return FittedMethod(**data)

class ComparisonSchema(Schema, DumpMixin):
    comparison_id = fields.Integer()
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
    seeds = fields.List(fields.Dict, allow_none=False)

    @post_load
    def make_model(self, data, **kwargs):
        return FittedModel(**data)


class VersionSchema(Schema, DumpMixin):
    class Meta:
        unknown = EXCLUDE

    version_id = fields.Integer()
    investigation_id = fields.Integer()
    iterations = fields.Integer(allow_none=True)
    steps = fields.Integer(allow_none=True)
    created_at = fields.DateTime()
    fitted_models = fields.List(fields.Nested(FittedModelSchema), allow_none=False, data_key='results')
    comparison = fields.Nested(ComparisonSchema, allow_none=False)

    @post_load
    def make_version(self, data, **kwargs) -> Version:
        return Version(**data)



FITTED_METHOD_SCHEMA = FittedMethodSchema()
COMPARISON_SCHEMA = ComparisonSchema()
FITTED_MODEL_SCHEMA = FittedModelSchema()
VERSION_SCHEMA = VersionSchema()

__all__ = ["FittedMethodSchema","FittedModelSchema", "ComparisonSchema"]
