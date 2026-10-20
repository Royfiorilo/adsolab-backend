from marshmallow import fields, Schema, validates_schema, pre_load, post_load, ValidationError
from marshmallow.validate import Range

from entities.kinetics_sample import KineticsSampleEntity
from entities.schemas.dump_mixin import DumpMixin
from database import db

# Negative readings above this limit are instrument noise and become 0; at or below it they are errors.
NOISE_LIMIT = 1.0


def zero_instrument_noise(values):
    """Turns values in (-NOISE_LIMIT, 0) into 0. Anything that is not a list of numbers is returned as is."""
    if not isinstance(values, list):
        return values
    return [
        0 if isinstance(v, (int, float)) and not isinstance(v, bool) and -NOISE_LIMIT < v < 0.0 else v
        for v in values
    ]


class KineticsSampleSchema(Schema, DumpMixin):
    kinetic_sample_id = fields.Integer(load_default=None)
    time = fields.List(fields.Float(), required=True, validate=lambda v: len(v) >= 2)
    qt = fields.List(fields.Float(), load_default=None)
    concentration = fields.List(fields.Float(), load_default=None)
    initial_concentration = fields.Float(load_default=None, validate=Range(min=0))
    volume = fields.Float(load_default=None, validate=Range(min=0, min_inclusive=False))
    adsorbent_mass = fields.Float(load_default=None, validate=Range(min=0, min_inclusive=False))

    title = fields.Str(load_default=None)
    description = fields.Str(load_default=None)
    temperature = fields.Float(load_default=None)
    time_unit = fields.Str(load_default=None)
    measure_unit = fields.Str(load_default=None)

    adsorbate_id = fields.Integer(required=True)
    adsorbent_id = fields.Integer(required=True)

    # Declaramos los campos como dump_only y pasamos por alto en load
    adsorbate = fields.Method("get_adsorbate_name", dump_only=True, load_default=None)
    adsorbent = fields.Method("get_adsorbent_name", dump_only=True, load_default=None)

    deleted_at = fields.DateTime(load_default=None)
    user_id = fields.Integer(load_default=None)

    def get_adsorbate_name(self, obj):
        if isinstance(obj, dict):
            return obj.get('adsorbate') or obj.get('adsorbate_name')
        if hasattr(obj, 'adsorbate') and obj.adsorbate:
            if isinstance(obj.adsorbate, dict):
                return obj.adsorbate.get('iupac_name') or obj.adsorbate.get('ion_name')
            return getattr(obj.adsorbate, 'iupac_name', getattr(obj.adsorbate, 'ion_name', None))
        
        if hasattr(obj, 'adsorbate_id') and obj.adsorbate_id:
            try:
                if db.session and hasattr(db.session, 'get'):
                    from entities.adsorbate import Adsorbate
                    adsorbate = db.session.get(Adsorbate, obj.adsorbate_id)
                    return adsorbate.iupac_name if adsorbate else None
            except Exception:
                return None
        return None

    def get_adsorbent_name(self, obj):
        if isinstance(obj, dict):
            return obj.get('adsorbent') or obj.get('adsorbent_name')
        if hasattr(obj, 'adsorbent') and obj.adsorbent:
            if isinstance(obj.adsorbent, dict):
                return obj.adsorbent.get('name')
            return getattr(obj.adsorbent, 'name', None)
            
        if hasattr(obj, 'adsorbent_id') and obj.adsorbent_id:
            try:
                if db.session and hasattr(db.session, 'get'):
                    from entities.adsorbent import Adsorbent
                    adsorbent = db.session.get(Adsorbent, obj.adsorbent_id)
                    return adsorbent.name if adsorbent else None
            except Exception:
                return None
        return None

    @pre_load
    def normalize_numbers(self, data, **kwargs):
        for field_name in ['time', 'qt', 'concentration']:
            if field_name in data:
                data[field_name] = zero_instrument_noise(data[field_name])
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
        if data.get('concentration') is not None and any(v < 0 for v in data['concentration']):
            raise ValidationError('concentration values must be non-negative.')

    @post_load
    def make_sample(self, data, **kwargs):
        # Excluimos los campos de solo lectura antes de instanciar la entidad
        data.pop('adsorbate', None)
        data.pop('adsorbent', None)
        return KineticsSampleEntity(**data)


KINETICS_SAMPLE_SCHEMA = KineticsSampleSchema()