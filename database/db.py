import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        import streamlit as st

        DATABASE_URL = st.secrets.get("DATABASE_URL")
    except Exception:
        pass

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Please set it in .env or Streamlit Secrets."
    )

# Create engine
engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initializes the database by creating tables if they do not exist."""
    from .models import Base
    from sqlalchemy import inspect, text

    Base.metadata.create_all(bind=engine)

    # Automatic migration checks
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
    except Exception as e:
        import logging

        logging.warning(f"Auto-migration check skipped or failed: {e}")


# Run schema initialization and migration check on module load
init_db()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
