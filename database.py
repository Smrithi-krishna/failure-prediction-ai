import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from models import Base

load_dotenv()

logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False)
engine: Engine | None = None


def configure_engine(database_url: str | None = None) -> Engine:
    """Create and cache the engine. Does not connect to the database."""
    global engine
    url = database_url or os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and set it."
        )
    try:
        new_engine = create_engine(url, pool_pre_ping=True)
    except Exception as exc:
        raise RuntimeError(
            "DATABASE_URL is invalid or unsupported by SQLAlchemy."
        ) from exc
    engine = new_engine
    SessionLocal.configure(bind=engine)
    return engine


def initialize_database() -> None:
    """Create all tables. Called once at application startup."""
    target = engine or configure_engine()
    try:
        Base.metadata.create_all(bind=target)
        inspector = inspect(target)
        with target.begin() as connection:
            for table in Base.metadata.sorted_tables:
                if table.name not in inspector.get_table_names():
                    continue
                existing = {column["name"] for column in inspector.get_columns(table.name)}
                for column in table.columns:
                    if column.name not in existing and not column.primary_key:
                        column_type = column.type.compile(dialect=target.dialect)
                        connection.execute(text(
                            f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS '
                            f'"{column.name}" {column_type}'
                        ))
    except Exception as exc:
        logger.exception("Database initialization failed")
        raise RuntimeError(
            "Database initialization failed. "
            "Check that PostgreSQL is running and DATABASE_URL is correct."
        ) from exc


def check_database() -> bool:
    """Return True if the database is reachable, False otherwise."""
    target = engine or configure_engine()
    try:
        with target.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False


def get_db():
    """FastAPI dependency that yields a database session."""
    if engine is None:
        raise RuntimeError(
            "Database engine is not configured. "
            "Ensure configure_engine() is called at startup."
        )
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
