from marshmallow import fields, Schema, validates_schema, pre_load, post_load, ValidationError

from entities.kinetics_sample import KineticsSampleEntity
from entities.schemas.dump_mixin import DumpMixin


class KineticsSampleSchema(Schema, DumpMixin):
    """
    Schema de validación y serialización para muestras cinéticas.

    Acepta `time + qt` directamente, o `time + concentration` con los
    parámetros necesarios para calcular `qt` (initial_concentration, volume,
    adsorbent_mass). La conversión real se realiza en `kinetics_sample_service`.
    """
    kinetic_sample_id = fields.Integer(load_default=None)
    time = fields.List(fields.Float(), required=True, validate=lambda v: len(v) >= 2)
    qt = fields.List(fields.Float(), load_default=None)
    concentration = fields.List(fields.Float(), load_default=None)
    initial_concentration = fields.Float(load_default=None)
    volume = fields.Float(load_default=None)
    adsorbent_mass = fields.Float(load_default=None)

    title = fields.Str(load_default=None)
    description = fields.Str(load_default=None)
    temperature = fields.Float(load_default=None)
    time_unit = fields.Str(load_default=None)
    measure_unit = fields.Str(load_default=None)

    adsorbate_id = fields.Integer(required=True)
    adsorbent_id = fields.Integer(required=True)
    deleted_at = fields.DateTime(load_default=None)
    user_id = fields.Integer(load_default=None)

    @pre_load
    def normalize_numbers(self, data, **kwargs):
        """Elimina valores muy cercanos a 0 negativos por redondeo de instrumento."""
        for field_name in ['time', 'qt', 'concentration']:
            if field_name in data and data[field_name] is not None:
                data[field_name] = [0 if -1.0 < v < 0.0 else v for v in data[field_name]]
        return data

    @validates_schema
    def validate_sample(self, data, **kwargs):
        self._validate_qt_or_concentration(data)
        self._validate_lengths(data)
        self._validate_non_negative(data)

    def _validate_qt_or_concentration(self, data):
        has_qt = data.get('qt') is not None
        has_concentration = data.get('concentration') is not None
        if not has_qt and not has_concentration:
            raise ValidationError('Either qt or concentration must be provided.')
        if has_concentration and not has_qt:
            for required in ['initial_concentration', 'volume', 'adsorbent_mass']:
                if data.get(required) is None:
                    raise ValidationError(
                        f'{required} is required when providing concentration instead of qt.'
                    )

    def _validate_lengths(self, data):
        time_len = len(data['time'])
        if data.get('qt') is not None and len(data['qt']) != time_len:
            raise ValidationError('time and qt must have the same length.')
        if data.get('concentration') is not None and len(data['concentration']) != time_len:
            raise ValidationError('time and concentration must have the same length.')

    def _validate_non_negative(self, data):
        if any(v < 0 for v in data['time']):
            raise ValidationError('time values must be non-negative.')
        if data.get('qt') is not None and any(v < 0 for v in data['qt']):
            raise ValidationError('qt values must be non-negative.')

    @post_load
    def make_sample(self, data, **kwargs):
        return KineticsSampleEntity(**data)


KINETICS_SAMPLE_SCHEMA = KineticsSampleSchema()
