"""pgvector column that also stores JSON text on SQLite (unit tests only)."""

import json

from pgvector.sqlalchemy import Vector
from sqlalchemy.types import Text, TypeDecorator


class EmbeddingColumn(TypeDecorator):
    """Store embeddings as pgvector on PostgreSQL.

    SQLite is used only by unit tests, which never run similarity search.
    """

    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return Vector(self.dimensions)
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        floats = [float(item) for item in value]
        if len(floats) != self.dimensions:
            raise ValueError(
                f"Embedding has {len(floats)} dimensions; expected {self.dimensions}."
            )
        if dialect.name == "postgresql":
            return floats
        return json.dumps(floats)

    def process_result_value(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        if isinstance(value, str):
            loaded = json.loads(value)
            return [float(item) for item in loaded]
        return [float(item) for item in value]
