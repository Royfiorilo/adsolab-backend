from sqlalchemy.orm import Query


class DumpMixin:
    @classmethod
    def with_schema(cls, schema):
        class SchemaQuery(Query):
            def __iter__(self):
                return iter(schema.dump(list(super().__iter__()), many=True))

            def first(self):
                result = super().first()
                return schema.dump(result) if result else None

        return SchemaQuery(cls)
