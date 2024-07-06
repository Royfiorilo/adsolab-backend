from marshmallow import fields, post_load, Schema

from app.entities.investigation import InvestigationEntity
from app.entities.schemas.fitted_model_schema import FittedModelSchema


class InvestigationSchema(Schema):
    investigation_id = fields.Integer(dump_only=True)
    sample_id = fields.Integer()
    #fitted_models = fields.Nested("FittedModelSchema")

    @post_load
    def make_investigation(self, data):
        return InvestigationEntity(**data)


INVESTIGATION_SCHEMA = InvestigationSchema()

__all__ = ["FittedModelSchema"]
