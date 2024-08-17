from sqlalchemy.orm import Query
import app


class DumpMixin:
    @classmethod
    def with_schema(cls, schema):
        class SchemaQuery(Query):
            def __init__(self, entities, session=None, schema=None):
                super().__init__(entities, session=session)
                self._schema = schema

            def __iter__(self):
                results = list(super().__iter__())
                if self._schema:
                    return iter(self._schema.dump(results, many=True))
                return iter(results)

            def first(self):
                result = super().first()
                if self._schema and result:
                    return self._schema.dump(result)
                return result

        return SchemaQuery(cls, session=app.db.session)
