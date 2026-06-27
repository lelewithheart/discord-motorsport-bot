"""
Core data models for the Discord Motorsport Universe.
All entities are defined as dataclasses with type hints.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from decimal import Decimal


# ─── Enums ────────────────────────────────────────────────────────────────

class League(str, Enum):
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"

    @property
    def level(self) -> int:
        return int(self.value[1:])

    @property
    def qualifier_penalty_ms(self) -> int:
        """Penalty in ms for AFK teams, by league level."""
        return int(1500 + (self.level - 1) * 350)

    @property
    def base_lap_time_ms(self) -> int:
        """Base lap time decreases as league gets higher (faster)."""
        return 95000 - (10 - self.level) * 800

    def __lt__(self, other):
        if isinstance(other, League):
            return self.level < other.level
        return NotImplemented


class Weather(str, Enum):
    DRY = "dry"
    CLOUDS = "clouds"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    STORM = "storm"


class Personality(str, Enum):
    CALM = "calm"
    AGGRESSIVE = "aggressive"
    INCONSISTENT = "inconsistent"
    STRATEGIC = "strategic"
    CLUTCH = "clutch"


class SponsorType(str, Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    GLOBAL = "global"
    MEGA = "mega"
    TITLE = "title"


class SeasonPhase(str, Enum):
    PRE_SEASON = "pre_season"
    SEASON_ACTIVE = "season_active"
    QUALIFIER = "qualifier"
    POST_SEASON = "post_season"


class DriverSlot(int, Enum):
    MAIN_1 = 1
    MAIN_2 = 2
    RESERVE = 3


class UpgradeType(str, Enum):
    AERODYNAMICS = "aerodynamics"
    ENGINE = "engine"
    SIMULATOR = "simulator"
    PIT_CREW = "pit_crew"
    SCOUTING = "scouting"


# ─── Driver ───────────────────────────────────────────────────────────────

@dataclass
class DriverAttributes:
    """Visible driver attributes (0-100)."""
    speed: int = 50
    consistency: int = 50
    racecraft: int = 50
    overtaking: int = 50
    tyre_management: int = 50
    qualifying_pace: int = 50
    wet_performance: int = 50
    mental_strength: int = 50

    def overall(self) -> float:
        return sum(self.__dict__.values()) / len(self.__dataclass_fields__)

    def increase(self, attr: str, amount: int, max_val: int = 99):
        current = getattr(self, attr)
        setattr(self, attr, min(max_val, current + amount))

    def decrease(self, attr: str, amount: int, min_val: int = 10):
        current = getattr(self, attr)
        setattr(self, attr, max(min_val, current - amount))


@dataclass
class HiddenStats:
    """Hidden driver stats that influence development."""
    potential: int = 50       # 0-100, maximum achievable overall
    growth_rate: float = 1.0  # 0.1-1.5
    aggression: int = 50      # 0-100, crash risk
    risk_taking: int = 50     # 0-100, risky maneuvers
    pressure_handling: int = 50  # 0-100, performance under pressure


PERSONALITY_MODIFIERS = {
    Personality.CALM: {"consistency": 5, "risk_taking": -20},
    Personality.AGGRESSIVE: {"overtaking": 10, "aggression": 20, "risk_taking": 15},
    Personality.INCONSISTENT: {"consistency": -15},  # variance_mult handled separately
    Personality.STRATEGIC: {"tyre_management": 10, "racecraft": 10},
    Personality.CLUTCH: {"mental_strength": 15, "pressure_handling": 20},
}


@dataclass
class Driver:
    """A driver in the motorsport universe."""
    id: str
    first_name: str
    last_name: str
    nationality: str
    age: int
    attributes: DriverAttributes = field(default_factory=DriverAttributes)
    hidden: HiddenStats = field(default_factory=HiddenStats)
    personality: Personality = Personality.CALM
    slot: Optional[DriverSlot] = None
    team_id: Optional[str] = None
    morale: int = 50
    is_academy: bool = False
    is_retired: bool = False
    retirement_season: Optional[int] = None

    # Career stats
    wins: int = 0
    podiums: int = 0
    races_driven: int = 0

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age_group(self) -> str:
        if self.age <= 19:
            return "rookie"
        elif self.age <= 22:
            return "developing"
        elif self.age <= 27:
            return "peak"
        elif self.age <= 30:
            return "late_peak"
        elif self.age <= 35:
            return "veteran"
        else:
            return "decline"

    def apply_personality_modifiers(self):
        """Apply personality bonuses to base attributes."""
        mods = PERSONALITY_MODIFIERS.get(self.personality, {})
        for attr, bonus in mods.items():
            if hasattr(self.attributes, attr):
                current = getattr(self.attributes, attr)
                setattr(self.attributes, attr, max(0, min(99, current + bonus)))


# ─── Sponsor ──────────────────────────────────────────────────────────────

@dataclass
class Sponsor:
    """A team sponsor."""
    id: str
    name: str
    sponsor_type: SponsorType
    budget: Decimal        # per season
    contract_seasons: int = 1
    seasons_remaining: int = 1
    min_performance: int = 0   # min team performance rating required
    min_league: int = 10       # min league level (10 = F10 is lowest)
    driver_nationality_bonus: bool = False
    bonus_per_win: Decimal = Decimal("0")
    bonus_per_podium: Decimal = Decimal("0")


# ─── Team ─────────────────────────────────────────────────────────────────

@dataclass
class TeamUpgrade:
    upgrade_type: UpgradeType
    level: int = 1


UPGRADE_COSTS = {
    UpgradeType.AERODYNAMICS: [500_000, 800_000, 1_200_000, 1_700_000, 2_300_000,
                                3_000_000, 3_800_000, 4_700_000, 5_700_000, 7_000_000],
    UpgradeType.ENGINE: [600_000, 1_000_000, 1_500_000, 2_200_000, 3_000_000,
                          4_000_000, 5_200_000, 6_500_000, 8_000_000, 10_000_000],
    UpgradeType.SIMULATOR: [400_000, 700_000, 1_100_000, 1_600_000, 2_200_000],
    UpgradeType.PIT_CREW: [200_000, 350_000, 550_000, 800_000, 1_100_000],
    UpgradeType.SCOUTING: [100_000, 250_000, 500_000],
}


@dataclass
class Team:
    """A player's team."""
    id: str
    name: str
    owner_id: int       # Discord User ID
    league: int = 10    # 1-10 (F1=1, F10=10)
    budget: Decimal = Decimal("1_000_000")
    performance_rating: int = 50
    infrastructure_level: int = 1

    # Personnel
    main_driver_1: Optional[Driver] = None
    main_driver_2: Optional[Driver] = None
    reserve_driver: Optional[Driver] = None

    # Finances
    sponsor_income: Decimal = Decimal("0")
    salary_costs: Decimal = Decimal("0")
    prize_money: Decimal = Decimal("0")

    # Stats
    wins: int = 0
    podiums: int = 0
    season_points: int = 0
    total_qualifier_time_ms: int = 0
    qualifier_count: int = 0

    # Premium
    is_premium: bool = False
    extra_slots: int = 0

    # Upgrades
    upgrades: dict[UpgradeType, TeamUpgrade] = field(default_factory=dict)

    # Season
    active_season: int = 1
    current_race: int = 0
    afk_streak: int = 0   # consecutive missed qualifiers

    @property
    def drivers(self) -> list[Driver]:
        return [d for d in [self.main_driver_1, self.main_driver_2, self.reserve_driver] if d]

    @property
    def league_enum(self) -> League:
        return League(f"F{self.league}")

    def get_upgrade_level(self, utype: UpgradeType) -> int:
        if utype in self.upgrades:
            return self.upgrades[utype].level
        return 0

    def get_upgrade_cost(self, utype: UpgradeType) -> Optional[int]:
        current = self.get_upgrade_level(utype)
        costs = UPGRADE_COSTS.get(utype, [])
        if current >= len(costs):
            return None  # max level
        return costs[current]

    def recalculate_performance(self):
        """Recalculate performance_rating from upgrades and drivers."""
        base = 40
        base += self.get_upgrade_level(UpgradeType.AERODYNAMICS) * 2
        base += self.get_upgrade_level(UpgradeType.ENGINE) * 3
        base += self.infrastructure_level * 2
        if self.main_driver_1:
            base += self.main_driver_1.attributes.overall() * 0.2
        if self.main_driver_2:
            base += self.main_driver_2.attributes.overall() * 0.15
        self.performance_rating = min(100, int(base))


# ─── Race & Qualifier Results ─────────────────────────────────────────────

@dataclass
class DriverRaceResult:
    driver_id: str
    position: int
    total_time_ms: int      # race total
    fastest_lap_ms: int
    dnfs: bool = False
    events: list[str] = field(default_factory=list)


@dataclass
class RaceResult:
    """Result of one offline race."""
    team_id: str
    season: int
    race_number: int
    track_name: str
    weather: Weather
    driver_1_result: Optional[DriverRaceResult] = None
    driver_2_result: Optional[DriverRaceResult] = None
    team_points: int = 0
    race_events: list[str] = field(default_factory=list)


@dataclass
class QualifierResult:
    """Result of one qualifier session."""
    id: str
    team_id: str
    league: int
    season: int
    race_number: int
    driver_1_time_ms: int
    driver_2_time_ms: int
    driver_3_time_ms: int
    average_time_ms: int
    was_auto: bool = False   # True if standard time was used


@dataclass
class TeamRank:
    """A team's standing in a season ranking."""
    team_id: str
    team_name: str
    total_time_ms: int
    average_time_ms: int
    qualifiers_run: int
    rank: int = 0
    league: int = 10


# ─── Season ───────────────────────────────────────────────────────────────

@dataclass
class SeasonState:
    """The global season state for a league."""
    league: int
    season: int
    phase: SeasonPhase = SeasonPhase.PRE_SEASON
    current_race: int = 0
    total_races: int = 12


# ─── World Event ──────────────────────────────────────────────────────────

@dataclass
class WorldEvent:
    """A dynamic world event affecting a driver, team, or league."""
    id: str
    event_type: str
    description: str
    season: int
    race_number: Optional[int] = None
    effects: dict = field(default_factory=dict)
    target_team_id: Optional[str] = None
    target_driver_id: Optional[str] = None


# ─── Academy ──────────────────────────────────────────────────────────────

@dataclass
class Scout:
    """An academy scout."""
    id: str
    team_id: str
    level: int = 1
    region: Optional[str] = None  # None = global
    cost_per_season: Decimal = Decimal("100_000")

    @property
    def bonus_per_driver(self) -> int:
        return self.level * 5

    @property
    def extra_drivers(self) -> int:
        return self.level  # 1/2/3 extra drivers per drop
