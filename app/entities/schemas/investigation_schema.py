from marshmallow import fields, post_load


class InvestigationSchema():
    _id = fields.Str()
    sample = fields.Nested("SampleSchema")

    @post_load
    def make_investigation(self, data, **kwargs):
        return Investigation(**data)


EVALUATION_SCHEMA = InvestigationSchema()


