"""
SQLAlchemy ORM models for the Discord Motorsport Universe.
Maps all dataclasses to database tables for persistence.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Text,
    BigInteger, Enum as SAEnum, ForeignKey, UniqueConstraint, JSON,
    DECIMAL, Index
)
from sqlalchemy.orm import relationship
from motorsport.data.database import Base
from motorsport.models import (
    League, Weather, Personality, SponsorType, SeasonPhase, UpgradeType
)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Player ────────────────────────────────────────────────────────────────

class PlayerModel(Base):
    __tablename__ = "players"

    id = Column(BigInteger, primary_key=True)  # Discord User ID
    username = Column(String(128), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    premium_since = Column(DateTime, nullable=True)
    total_seasons = Column(Integer, default=0)
    locale = Column(String(10), default="de")

    teams = relationship("TeamModel", back_populates="owner", cascade="all, delete-orphan")


# ─── Team ──────────────────────────────────────────────────────────────────

class TeamModel(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=_uuid)
    owner_id = Column(BigInteger, ForeignKey("players.id"), nullable=False)
    name = Column(String(64), nullable=False)
    league = Column(Integer, default=10, nullable=False)  # 1=F1, 10=F10

    # Performance
    budget = Column(DECIMAL(14, 2), default=1_000_000.00)
    performance_rating = Column(Integer, default=50)
    infrastructure_level = Column(Integer, default=1)

    # Finances
    sponsor_income = Column(DECIMAL(12, 2), default=0)
    salary_costs = Column(DECIMAL(12, 2), default=0)
    prize_money = Column(DECIMAL(12, 2), default=0)

    # Stats
    wins = Column(Integer, default=0)
    podiums = Column(Integer, default=0)
    season_points = Column(Integer, default=0)
    total_qualifier_time_ms = Column(BigInteger, default=0)
    qualifier_count = Column(Integer, default=0)

    # Premium
    is_premium = Column(Boolean, default=False)
    extra_slots = Column(Integer, default=0)

    # Season state
    active_season = Column(Integer, default=1)
    current_race = Column(Integer, default=0)
    afk_streak = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("PlayerModel", back_populates="teams")
    drivers = relationship("DriverModel", back_populates="team", cascade="all, delete-orphan")
    sponsors = relationship("SponsorModel", back_populates="team", cascade="all, delete-orphan")
    upgrades = relationship("TeamUpgradeModel", back_populates="team", cascade="all, delete-orphan")
    qualifiers = relationship("QualifierModel", back_populates="team", cascade="all, delete-orphan")
    setups = relationship("SetupModel", back_populates="team", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSessionModel", back_populates="team", cascade="all, delete-orphan")
    rnd_upgrades = relationship("RndUpgradeModel", back_populates="team", cascade="all, delete-orphan")
    rnd_points = relationship("RndPointsModel", back_populates="team", cascade="all, delete-orphan")


# ─── Driver ────────────────────────────────────────────────────────────────

class DriverModel(Base):
    __tablename__ = "drivers"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)

    # Identity
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    nationality = Column(String(4), nullable=False)
    age = Column(Integer, nullable=False)

    # Visible attributes (0-100)
    speed = Column(Integer, default=50)
    consistency = Column(Integer, default=50)
    racecraft = Column(Integer, default=50)
    overtaking = Column(Integer, default=50)
    tyre_management = Column(Integer, default=50)
    qualifying_pace = Column(Integer, default=50)
    wet_performance = Column(Integer, default=50)
    mental_strength = Column(Integer, default=50)

    # Hidden stats
    potential = Column(Integer, default=50)
    growth_rate = Column(Float, default=1.0)
    aggression = Column(Integer, default=50)
    risk_taking = Column(Integer, default=50)
    pressure_handling = Column(Integer, default=50)

    # Status
    personality = Column(String(20), default="calm")
    slot = Column(Integer, nullable=True)  # 1=Main1, 2=Main2, 3=Reserve
    morale = Column(Integer, default=50)
    is_academy = Column(Boolean, default=False)
    is_retired = Column(Boolean, default=False)
    retirement_season = Column(Integer, nullable=True)

    # Career
    wins = Column(Integer, default=0)
    podiums = Column(Integer, default=0)
    races_driven = Column(Integer, default=0)

    # Season
    season = Column(Integer, default=1)

    # Relationships
    team = relationship("TeamModel", back_populates="drivers")

    __table_args__ = (
        Index("idx_driver_team", "team_id"),
    )


# ─── Sponsor ───────────────────────────────────────────────────────────────

class SponsorModel(Base):
    __tablename__ = "sponsors"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)

    name = Column(String(128), nullable=False)
    sponsor_type = Column(String(20), nullable=False)
    budget = Column(DECIMAL(14, 2), nullable=False)
    contract_seasons = Column(Integer, default=1)
    seasons_remaining = Column(Integer, default=1)
    min_performance = Column(Integer, default=0)
    min_league = Column(Integer, default=10)
    driver_nationality_bonus = Column(Boolean, default=False)
    bonus_per_win = Column(DECIMAL(12, 2), default=0)
    bonus_per_podium = Column(DECIMAL(12, 2), default=0)
    signed_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("TeamModel", back_populates="sponsors")


# ─── Team Upgrade ──────────────────────────────────────────────────────────

class TeamUpgradeModel(Base):
    __tablename__ = "team_upgrades"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    upgrade_type = Column(String(20), nullable=False)
    level = Column(Integer, default=1)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("TeamModel", back_populates="upgrades")

    __table_args__ = (
        UniqueConstraint("team_id", "upgrade_type", name="uq_team_upgrade"),
    )


# ─── Qualifier ─────────────────────────────────────────────────────────────

class QualifierModel(Base):
    __tablename__ = "qualifiers"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    league = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)

    driver_1_time_ms = Column(BigInteger, nullable=False)
    driver_2_time_ms = Column(BigInteger, nullable=False)
    driver_3_time_ms = Column(BigInteger, nullable=False)
    average_time_ms = Column(BigInteger, nullable=False)

    was_auto = Column(Boolean, default=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("TeamModel", back_populates="qualifiers")

    __table_args__ = (
        Index("idx_qualifier_lookup", "league", "season", "race_number"),
    )


# ─── Race Result ───────────────────────────────────────────────────────────

class RaceResultModel(Base):
    __tablename__ = "race_results"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)
    track_name = Column(String(64))
    weather = Column(String(20), default="dry")

    driver_1_position = Column(Integer)
    driver_2_position = Column(Integer)
    driver_1_time_ms = Column(BigInteger)
    driver_2_time_ms = Column(BigInteger)
    team_points = Column(Integer, default=0)

    race_events = Column(JSON, default=list)
    simulated_at = Column(DateTime, default=datetime.utcnow)


# ─── Season Ranking ────────────────────────────────────────────────────────

class SeasonRankingModel(Base):
    __tablename__ = "season_rankings"

    id = Column(String(36), primary_key=True, default=_uuid)
    league = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)

    total_time_ms = Column(BigInteger, nullable=False)
    average_time_ms = Column(BigInteger, nullable=False)
    rank = Column(Integer, nullable=False)

    promotion_eligible = Column(Boolean, default=False)
    relegation_eligible = Column(Boolean, default=False)
    new_league = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("league", "season", "team_id", name="uq_season_rank"),
    )


# ─── World Event ───────────────────────────────────────────────────────────

class WorldEventModel(Base):
    __tablename__ = "world_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)
    event_type = Column(String(40), nullable=False)
    description = Column(Text, nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=True)
    effects = Column(JSON, default=dict)
    happened_at = Column(DateTime, default=datetime.utcnow)


# ─── Transfer History ──────────────────────────────────────────────────────

class TransferModel(Base):
    __tablename__ = "transfer_history"

    id = Column(String(36), primary_key=True, default=_uuid)
    driver_id = Column(String(36), nullable=False)
    from_team_id = Column(String(36), nullable=True)
    to_team_id = Column(String(36), nullable=False)
    fee = Column(DECIMAL(12, 2), default=0)
    season = Column(Integer, nullable=False)
    transferred_at = Column(DateTime, default=datetime.utcnow)


# ─── Academy Scout ─────────────────────────────────────────────────────────

class ScoutModel(Base):
    __tablename__ = "academy_scouts"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    level = Column(Integer, default=1)
    region = Column(String(30), nullable=True)
    cost_per_season = Column(DECIMAL(12, 2), default=100_000)
    hired_at = Column(DateTime, default=datetime.utcnow)


# ─── Track ──────────────────────────────────────────────────────────────────

class TrackModel(Base):
    __tablename__ = "tracks"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(64), nullable=False, unique=True)
    country = Column(String(64))
    req_speed = Column(Float, default=0.5)
    req_acceleration = Column(Float, default=0.5)
    req_downforce = Column(Float, default=0.5)
    req_braking = Column(Float, default=0.5)
    req_tyre_management = Column(Float, default=0.5)
    lap_length_km = Column(Float, default=5.0)


# ─── Setup ──────────────────────────────────────────────────────────────────

class SetupModel(Base):
    __tablename__ = "setups"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=True)
    name = Column(String(64), default="Default")
    front_wing = Column(Integer, default=10)
    rear_wing = Column(Integer, default=10)
    suspension = Column(Integer, default=10)
    gear_ratio = Column(Integer, default=10)
    tire_compound = Column(Integer, default=10)
    is_default = Column(Boolean, default=False)

    team = relationship("TeamModel", back_populates="setups")


# ─── Training Session ───────────────────────────────────────────────────────

class TrainingSessionModel(Base):
    __tablename__ = "training_sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)
    lap_count = Column(Integer, default=0)
    best_lap_ms = Column(Integer, nullable=True)
    avg_lap_ms = Column(Integer, nullable=True)
    setup_id = Column(String(36), ForeignKey("setups.id"), nullable=True)
    session_date = Column(DateTime, default=datetime.utcnow)

    team = relationship("TeamModel", back_populates="training_sessions")


# ─── R&D Upgrades ───────────────────────────────────────────────────────────

class RndUpgradeModel(Base):
    __tablename__ = "rnd_upgrades"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    component = Column(String(32), nullable=False)
    level = Column(Integer, default=1)

    team = relationship("TeamModel", back_populates="rnd_upgrades")

    __table_args__ = (
        UniqueConstraint("team_id", "component", name="uq_team_component"),
    )


# ─── R&D Points ─────────────────────────────────────────────────────────────

class RndPointsModel(Base):
    __tablename__ = "rnd_points"

    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, nullable=False)
    points = Column(Integer, default=0)

    team = relationship("TeamModel", back_populates="rnd_points")

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_team_season_rnd"),
    )


# ─── Race Schedule ──────────────────────────────────────────────────────────

class RaceScheduleModel(Base):
    __tablename__ = "race_schedule"

    id = Column(String(36), primary_key=True, default=_uuid)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=False)
    race_date = Column(Date, nullable=False)
    qualifier_deadline = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
