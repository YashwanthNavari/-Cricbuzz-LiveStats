import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv

logger = logging.getLogger("db")


def _resolve_database_url() -> Optional[str]:
    """Resolve DATABASE_URL from .env first, then Streamlit secrets as fallback."""
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st

        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass
    return None


def _build_engine(database_url: str):
    """Build and return a SQLAlchemy engine for the given URL."""
    from sqlalchemy import create_engine

    engine_kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
    return create_engine(database_url, **engine_kwargs)


# --------------------------------------------------------------------------- #
# Lazy singletons — nothing is created at import time                          #
# --------------------------------------------------------------------------- #
_engine = None
_SessionLocal = None


def get_engine():
    """Return (and lazily create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = _resolve_database_url()
        if not url:
            raise ValueError(
                "DATABASE_URL is not configured. "
                "Add it to your .env file or to the Streamlit app Secrets panel "
                "(Settings → Secrets) in the format:\n"
                '  DATABASE_URL = "sqlite:///cricbuzz_db.sqlite"'
            )
        _engine = _build_engine(url)
    return _engine


def get_session_factory():
    """Return (and lazily create) the SQLAlchemy SessionLocal factory."""
    global _SessionLocal
    if _SessionLocal is None:
        from sqlalchemy.orm import sessionmaker

        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


def init_db() -> None:
    """Create all tables and run auto-migration checks.  Safe to call repeatedly."""
    from sqlalchemy import inspect, text

    from .models import Base

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    try:
        inspector = inspect(engine)
        if "matches" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("matches")]
            if "match_overs_limit" not in columns:
                with engine.begin() as conn:
                    conn.execute(
                        text("ALTER TABLE matches ADD COLUMN match_overs_limit INTEGER")
                    )
            if "player_of_the_match_id" not in columns:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE matches ADD COLUMN player_of_the_match_id INTEGER REFERENCES players(id)"
                        )
                    )

        if "innings" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("innings")]
            for col in ["extras", "wides", "no_balls", "byes", "leg_byes"]:
                if col not in columns:
                    with engine.begin() as conn:
                        conn.execute(
                            text(
                                f"ALTER TABLE innings ADD COLUMN {col} INTEGER DEFAULT 0"
                            )
                        )
    except Exception as exc:
        logger.warning("Auto-migration check skipped or failed: %s", exc)


@contextmanager
def get_db() -> Generator:
    """Provide a transactional database session scope."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
