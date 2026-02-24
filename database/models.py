"""SQLAlchemy ORM models for Nominis."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, declarative_base
import enum

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

    def __repr__(self):
        return f"<Name {self.text!r} ({self.gender.value})>"


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
    """

    __tablename__ = "name_combos"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    first_id = Column(Integer, ForeignKey("names.id"), nullable=False)
    middle_id = Column(Integer, ForeignKey("names.id"), nullable=False)
    elo_score = Column(Float, default=1000.0, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", "first_id", "middle_id", name="uq_combo"),
    )

    profile = relationship("Profile", back_populates="combos")
    first = relationship("Name", foreign_keys=[first_id])
    middle = relationship("Name", foreign_keys=[middle_id])

    def __repr__(self):
        return f"<NameCombo profile={self.profile_id} first={self.first_id} middle={self.middle_id} elo={self.elo_score:.1f}>"


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
