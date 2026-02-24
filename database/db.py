"""Database initialization and session management."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Profile, Setting

DB_PATH = Path.home() / ".nominis" / "nominis.db"

engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    _seed_defaults()


def get_session() -> Session:
    return SessionLocal()


def _seed_defaults():
    """Create default profiles and settings if not present."""
    with get_session() as s:
        if not s.query(Profile).first():
            s.add_all(
                [
                    Profile(id=1, label="Husband", accent_color="#89cff0"),
                    Profile(id=2, label="Wife", accent_color="#ffb6c1"),
                ]
            )
        defaults = {
            "surname": "Smith",
            "match_random_pct": "30",  # % chance of distal match
            "elo_spread_thresh": "50",  # std dev before blended matching kicks in
            "k_factor_default": "32",
            "k_factor_stable": "16",
            "k_stable_threshold": "20",  # match_count before reduced K
        }
        for k, v in defaults.items():
            if not s.get(Setting, k):
                s.add(Setting(key=k, value=v))
        s.commit()


def get_setting(key: str) -> str:
    with get_session() as s:
        row = s.get(Setting, key)
        return row.value if row else None


def set_setting(key: str, value: str):
    with get_session() as s:
        row = s.get(Setting, key)
        if row:
            row.value = value
        else:
            s.add(Setting(key=key, value=value))
        s.commit()
