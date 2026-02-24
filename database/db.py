"""Database initialization and session management."""

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base, Profile, Setting

DB_PATH = Path.home() / ".nominis" / "nominis.db"

engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)  # creates tables only if missing
    SessionLocal = sessionmaker(bind=engine)
    _migrate(engine)
    _seed_defaults()


def _migrate(eng):
    """Safely add columns introduced after initial release."""
    inspector = inspect(eng)
    with eng.connect() as conn:
        # v2: streak on name_combos
        combo_cols = {c["name"] for c in inspector.get_columns("name_combos")}
        if "streak" not in combo_cols:
            conn.execute(
                text(
                    "ALTER TABLE name_combos ADD COLUMN streak INTEGER NOT NULL DEFAULT 0"
                )
            )
            conn.commit()

        # v3: slot-agnostic reputation on names
        name_cols = {c["name"] for c in inspector.get_columns("names")}
        if "rep_wins" not in name_cols:
            conn.execute(
                text("ALTER TABLE names ADD COLUMN rep_wins INTEGER NOT NULL DEFAULT 0")
            )
            conn.commit()
        if "rep_losses" not in name_cols:
            conn.execute(
                text(
                    "ALTER TABLE names ADD COLUMN rep_losses INTEGER NOT NULL DEFAULT 0"
                )
            )
            conn.commit()


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
            "match_random_pct": "25",
            "elo_spread_thresh": "50",
            # Higher K so scores spread quickly with large pools
            "k_factor_default": "64",
            "k_factor_stable": "32",
            "k_stable_threshold": "30",
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
