"""SQLAlchemy ORM models for Nominis."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Gender(enum.Enum):
    M = "M"
    F = "F"
    N = "N"


class Name(Base):
    __tablename__ = "names"

    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False, unique=True)
    gender = Column(SAEnum(Gender), nullable=False, default=Gender.N)
    skip_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Slot-agnostic reputation — incremented whenever any combo
    # containing this name (as first OR middle) wins or loses.
    rep_wins = Column(Integer, default=0, nullable=False)
    rep_losses = Column(Integer, default=0, nullable=False)

    @property
    def reputation(self) -> float:
        """
        Score in roughly [0.2, 2.0].
          Neutral (no matches) → 1.0
          Pure winner          → approaches 2.0
          Pure loser           → approaches 0.2
        Uses Laplace smoothing so new names start neutral.
        """
        total = self.rep_wins + self.rep_losses
        if total == 0:
            return 1.0
        win_rate = (self.rep_wins + 1) / (total + 2)  # Laplace smoothed
        return 0.2 + 1.8 * win_rate  # map [0,1] → [0.2, 2.0]

    def __repr__(self):
        return f"<Name {self.text!r} ({self.gender.value}) rep={self.reputation:.2f}>"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False, unique=True)
    accent_color = Column(String, nullable=False, default="#89cff0")

    combos = relationship(
        "NameCombo", back_populates="profile", cascade="all, delete-orphan"
    )
    matches = relationship("Match", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.label!r}>"


class NameCombo(Base):
    """
    An ordered (first, middle) name pair ranked per profile.
    'George Alabaster' and 'Alabaster George' are distinct rows.

    streak > 0  →  consecutive wins  (hot, fast-tracked upward)
    streak < 0  →  consecutive losses (cold, soft-suppressed)
    streak = 0  →  neutral
    """

    __tablename__ = "name_combos"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    first_id = Column(Integer, ForeignKey("names.id"), nullable=False)
    middle_id = Column(Integer, ForeignKey("names.id"), nullable=False)
    elo_score = Column(Float, default=1000.0, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", "first_id", "middle_id", name="uq_combo"),
    )

    profile = relationship("Profile", back_populates="combos")
    first = relationship("Name", foreign_keys=[first_id])
    middle = relationship("Name", foreign_keys=[middle_id])

    def __repr__(self):
        return (
            f"<NameCombo profile={self.profile_id} "
            f"first={self.first_id} middle={self.middle_id} "
            f"elo={self.elo_score:.1f} streak={self.streak}>"
        )


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    winner_combo_id = Column(Integer, ForeignKey("name_combos.id"), nullable=True)
    loser_combo_id = Column(Integer, ForeignKey("name_combos.id"), nullable=True)
    was_skip = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="matches")
    winner = relationship("NameCombo", foreign_keys=[winner_combo_id])
    loser = relationship("NameCombo", foreign_keys=[loser_combo_id])


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
