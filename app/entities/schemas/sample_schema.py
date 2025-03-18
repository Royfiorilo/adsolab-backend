from marshmallow import fields, post_load, validate, Schema, ValidationError, pre_load, validates_schema
from entities.sample import SampleEntity
from .dump_mixin import DumpMixin


class SampleSchema(Schema, DumpMixin):
    sample_id = fields.Integer(missing=None)
    ce = fields.List(
        fields.Float(), required=True, validate=validate.Length(min=1)
    )
    qe = fields.List(
        fields.Float(), required=True, validate=validate.Length(min=1)
    )
    title = fields.Str(missing=None)
    description = fields.Str(missing=None)
    temperature = fields.Float(missing=None)
    measure_unit = fields.Str(missing=None)
    adsorbate_id = fields.Integer(required=True)
    adsorbent_id = fields.Integer(required=True)
    deleted_at = fields.DateTime(missing=None)
    user_id = fields.Integer()

    @pre_load
    def normalize_numbers(self, data, **kwargs):
        for field in ['ce', 'qe']:
            if field in data:
                data[field] = self._normalize_field(data[field])
        return data

    def  _normalize_field(self, field_data):
        return [0 if -1.0 < num < 0.0 else num for num in field_data]

    @validates_schema
    def validate_sample(self, data, **kwargs):
        self._validate_lengths(data)
        self._validate_non_negative(data)

    def _validate_lengths(self, data):
        if len(data['ce']) != len(data['qe']):
            raise ValidationError('Ce and Qe must have the same length')

    def _validate_non_negative(self, data):
        for field in ['ce', 'qe']:
            if any(val < 0 for val in data[field]):
                raise ValidationError(f'Numbers in {field} cannot be negative')

    def _validate_non_ce_equals(self, data):
        ce_distinct = set(data['ce'])
        if len(data['ce']) != len(ce_distinct):
            raise ValidationError('Ce must have different values in all the points.')


    @post_load
    def make_sample(self, data, **kwargs):
        return SampleEntity(**data)


SAMPLE_SCHEMA = SampleSchema()
