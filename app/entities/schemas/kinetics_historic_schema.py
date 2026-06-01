from marshmallow import fields, Schema, post_load, EXCLUDE

from entities.schemas.dump_mixin import DumpMixin


class KineticsFittedMethodSchema(Schema, DumpMixin):
    """Schema para un método de ajuste individual dentro de un modelo cinético ajustado."""

    class Meta:
        unknown = EXCLUDE

    name = fields.Str(allow_none=False)
    parameters = fields.List(fields.Dict(), allow_none=False)
    statistics = fields.Dict(allow_none=False)
    residuals = fields.Dict(allow_none=False)
    transformed = fields.Dict(allow_none=True)
    success = fields.Bool(allow_none=False)


class KineticsFittedModelSchema(Schema, DumpMixin):
    """Schema para el resultado del ajuste de un modelo cinético."""
    kinetic_fitted_model_id = fields.Integer(load_default=None)
    model_id = fields.Integer(load_default=None)
    model_name = fields.Str(load_default=None)
    best_adjust = fields.Str(allow_none=False)
    seeds = fields.List(fields.Dict(), allow_none=False)
    adjustment_methods = fields.List(
        fields.Nested(KineticsFittedMethodSchema), allow_none=False
    )


class KineticsComparisonSchema(Schema, DumpMixin):
    """Schema para la comparación entre modelos cinéticos."""
    kinetic_comparison_id = fields.Integer(load_default=None)
    heuristic = fields.Dict(allow_none=False)
    ml = fields.Dict(allow_none=True, load_default=None)


class KineticsVersionSchema(Schema, DumpMixin):
    """Schema de una versión guardada de investigación cinética."""
    version_id = fields.Integer(load_default=None)
    kinetic_investigation_id = fields.Integer(load_default=None)
    iterations = fields.Integer(load_default=None)
    steps = fields.Float(load_default=None)
    created_at = fields.DateTime(load_default=None)
    fitted_models = fields.List(
        fields.Nested(KineticsFittedModelSchema), load_default=None
    )
    comparison = fields.Nested(KineticsComparisonSchema, load_default=None)


KINETICS_VERSION_SCHEMA = KineticsVersionSchema()
KINETICS_FITTED_MODEL_SCHEMA = KineticsFittedModelSchema()
KINETICS_COMPARISON_SCHEMA = KineticsComparisonSchema()
