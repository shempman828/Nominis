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

    profile_names = relationship(
        "ProfileName", back_populates="name", cascade="all, delete-orphan"
    )
    wins = relationship(
        "Match", foreign_keys="Match.winner_id", back_populates="winner"
    )
    losses = relationship(
        "Match", foreign_keys="Match.loser_id", back_populates="loser"
    )

    def __repr__(self):
        return f"<Name {self.text!r} ({self.gender.value})>"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False, unique=True)  # "Husband" | "Wife"
    accent_color = Column(String, nullable=False, default="#89cff0")

    profile_names = relationship(
        "ProfileName", back_populates="profile", cascade="all, delete-orphan"
    )
    matches = relationship("Match", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.label!r}>"


class ProfileName(Base):
    """Per-profile Elo score for each name."""

    __tablename__ = "profile_names"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    name_id = Column(Integer, ForeignKey("names.id"), nullable=False)
    elo_score = Column(Float, default=1000.0, nullable=False)
    match_count = Column(Integer, default=0, nullable=False)

    profile = relationship("Profile", back_populates="profile_names")
    name = relationship("Name", back_populates="profile_names")

    def __repr__(self):
        return f"<ProfileName profile={self.profile_id} name={self.name_id} elo={self.elo_score:.1f}>"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("names.id"), nullable=True)  # None = skip
    loser_id = Column(Integer, ForeignKey("names.id"), nullable=True)  # None = skip
    was_skip = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="matches")
    winner = relationship("Name", foreign_keys=[winner_id], back_populates="wins")
    loser = relationship("Name", foreign_keys=[loser_id], back_populates="losses")


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
