"""SQLAlchemy engine, sessions, and PostgreSQL + pgvector initialization."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


settings = get_settings()
engine = create_db_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def enable_pgvector(target_engine=None) -> None:
    """Enable the vector extension if this is PostgreSQL and it is missing.

    CREATE EXTENSION is skipped when the extension is already installed.
    On the pgvector Docker image it is often already present, and creating
    it again inside a transaction can raise a duplicate-key error.
    """
    target = engine if target_engine is None else target_engine
    if target.dialect.name != "postgresql":
        return
    with target.connect() as connection:
        existing = connection.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).first()
        if existing is not None:
            return
        try:
            connection.execute(text("CREATE EXTENSION vector"))
            connection.commit()
        except IntegrityError:
            connection.rollback()
            existing = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first()
            if existing is None:
                raise


def init_db() -> None:
    """Create the pgvector extension (PostgreSQL) and any missing tables.

    Alembic is not used in Phase 1. Changing EMBEDDING_DIMENSION after the
    tables exist requires a new database or a manual column change, because
    pgvector fixes the dimension on the column.
    """
    enable_pgvector(engine)
    # Import models so they are registered on Base before create_all.
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        _create_vector_index()


def _create_vector_index() -> None:
    statement = text(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )
    try:
        with engine.begin() as connection:
            connection.execute(statement)
    except Exception:
        logger.warning(
            "Could not create the HNSW index. Similarity search still works; "
            "it will scan the embedding column until the index exists."
        )


def database_status() -> str:
    """Return a short connectivity label for the health endpoint."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if connection.dialect.name == "postgresql":
                found = connection.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                ).first()
                if found is None:
                    return "connected_without_pgvector"
        return "connected"
    except Exception as exc:
        logger.warning("Database health check failed (%s)", type(exc).__name__)
        return "unavailable"


def ensure_database_available(db) -> None:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Database check failed (%s)", type(exc).__name__)
        raise DatabaseUnavailableError(
            "Database connection failed. Check DATABASE_URL and that PostgreSQL is running."
        ) from exc
