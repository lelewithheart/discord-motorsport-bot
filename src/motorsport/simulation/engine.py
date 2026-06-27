"""
Core simulation engine for the Discord Motorsport Universe.
Handles lap time calculation, race simulation, and qualifier simulation.
"""
from __future__ import annotations
import random
import uuid
import hashlib
from typing import Optional
from motorsport.models import (
    Driver, Team, League, Weather,
    RaceResult, DriverRaceResult, QualifierResult,
)

ALL_ATTRIBUTES_LIST = [
    "speed", "consistency", "racecraft", "overtaking",
    "tyre_management", "qualifying_pace", "wet_performance", "mental_strength"
]

# Weather effects on lap time
WEATHER_PENALTIES_MS = {
    Weather.DRY: 0,
    Weather.CLOUDS: 100,
    Weather.LIGHT_RAIN: 500,
    Weather.HEAVY_RAIN: 1500,
    Weather.STORM: 3000,
}

# Weather probabilities
WEATHER_ROLL = [
    (Weather.DRY, 0.50),
    (Weather.CLOUDS, 0.20),
    (Weather.LIGHT_RAIN, 0.15),
    (Weather.HEAVY_RAIN, 0.10),
    (Weather.STORM, 0.05),
]

# Track names (for race ambiance)
TRACK_NAMES = [
    "Monza", "Silverstone", "Spa", "Monaco", "Suzuka", "Interlagos",
    "Melbourne", "Bahrain", "Singapore", "Austin", "Montreal",
    "Abu Dhabi", "Barcelona", "Zandvoort", "Imola", "Red Bull Ring",
    "Hungaroring", "Baku", "Jeddah", "Miami", "Las Vegas", "Lusail",
    "Shanghai", "Sepang", "Kyalami", "Buenos Aires", "Portimão",
    "Nürburgring", "Le Mans", "Brands Hatch",
]


class SimSeed:
    """Deterministic seed generation for reproducible simulations."""

    @staticmethod
    def for_race(season: int, race_number: int, universe_id: str) -> int:
        key = f"{universe_id}:S{season}:R{race_number}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    @staticmethod
    def for_qualifier(season: int, race_number: int, league: int, team_id: str) -> int:
        key = f"QUAL:{season}:{race_number}:L{league}:{team_id}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    @staticmethod
    def for_driver_gen(season: int, sub_region: str) -> int:
        key = f"DRIVERGEN:S{season}:{sub_region}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    @staticmethod
    def for_weather(season: int, race_number: int) -> int:
        key = f"WEATHER:S{season}:R{race_number}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


class WeatherSystem:
    """Generates weather for races."""

    @staticmethod
    def roll_weather(season: int, race_number: int, 
                     climate_bias: Optional[str] = None) -> Weather:
        seed = SimSeed.for_weather(season, race_number)
        rng = random.Random(seed)
        roll = rng.random()

        # Adjust probabilities based on climate
        weights = list(zip(*WEATHER_ROLL))[1]  # default weights
        types = list(zip(*WEATHER_ROLL))[0]

        if climate_bias == "tropical":
            # More rain in tropics
            weights = [0.30, 0.15, 0.25, 0.20, 0.10]
        elif climate_bias == "desert":
            # Mostly dry
            weights = [0.70, 0.15, 0.08, 0.05, 0.02]
        elif climate_bias == "northern":
            # Cooler, more rain
            weights = [0.35, 0.20, 0.25, 0.15, 0.05]

        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if roll <= cumulative:
                return types[i]
        return Weather.DRY


class SimulationEngine:
    """Deterministic simulation engine for races and qualifiers."""

    def __init__(self, universe_id: str = "default"):
        self.universe_id = universe_id

    def simulate_qualifier_lap(self, driver: Driver, team: Team,
                                season: int, race_number: int,
                                weather: Weather) -> int:
        """Simulate a SINGLE qualifier lap in milliseconds."""
        seed = SimSeed.for_qualifier(
            season, race_number, team.league, team.id
        )
        rng = random.Random(seed + hash(driver.id) % 10000)

        league = League(f"F{team.league}")
        base_time = league.base_lap_time_ms

        # Driver skill bonus (0-5000ms)
        driver_bonus = self._calc_qualifying_bonus(driver, weather)

        # Team bonus (0-2000ms)
        team_bonus = team.performance_rating * 20

        # Random variance (normal distribution)
        variance = int(rng.gauss(0, 500))

        # Personality-based variance
        if driver.personality.value == "inconsistent":
            variance *= 2

        # Weather penalty
        weather_penalty = WEATHER_PENALTIES_MS.get(weather, 0)
        if weather != Weather.DRY:
            wet_factor = 1 - (driver.attributes.wet_performance / 100 * 0.5)
            weather_penalty = int(weather_penalty * wet_factor)

        # Mental strength bonus under pressure (qualifier = pressure)
        if driver.hidden.pressure_handling > 70:
            pressure_bonus = int(driver.hidden.pressure_handling * 3)
            driver_bonus += pressure_bonus

        lap_time = base_time - driver_bonus - team_bonus + variance + weather_penalty

        return max(60000, int(lap_time))

    def simulate_race(self, team: Team, season: int, race_number: int,
                      track: Optional[str] = None,
                      weather: Optional[Weather] = None) -> RaceResult:
        """Simulate a full race for a team's two main drivers."""
        if weather is None:
            weather = WeatherSystem.roll_weather(season, race_number)

        seed = SimSeed.for_race(season, race_number, self.universe_id)
        rng = random.Random(seed)
        track = track or rng.choice(TRACK_NAMES)

        d1 = team.main_driver_1
        d2 = team.main_driver_2

        results = []
        race_events = []

        for driver in [d1, d2]:
            if driver is None:
                continue

            # Base race pace
            driver_rng = random.Random(seed + hash(driver.id) % 10000)

            race_speed = self._calc_race_pace(driver, team, weather)

            # Overtaking performance
            overtake_bonus = driver.attributes.overtaking * 0.5

            # Tyre management affects consistency over race
            tyre_factor = driver.attributes.tyre_management / 100

            # Random incidents
            incident_chance = (driver.hidden.aggression + driver.hidden.risk_taking) / 400
            dnf = driver_rng.random() < incident_chance * 0.05

            # Calculate total race time
            race_length = 20 + team.league * 5  # 25-70 laps based on league
            lap_time = race_speed - overtake_bonus * 0.3
            total = int(lap_time * race_length * (1 - 0.1 * (1 - tyre_factor)))

            # Fastest lap (slightly faster than average)
            fastest = int(lap_time - rng.randint(200, 800))

            events = []
            if dnf:
                events.append(f"{driver.full_name} crashed out on lap {rng.randint(3, race_length - 1)}")
                total = 999999999  # DNF penalty

            results.append(DriverRaceResult(
                driver_id=driver.id,
                position=0,  # assigned externally
                total_time_ms=total,
                fastest_lap_ms=fastest,
                dnfs=dnf,
                events=events,
            ))

        # Assign positions based on total time
        results.sort(key=lambda r: r.total_time_ms)
        for i, r in enumerate(results):
            r.position = i + 1

        # Calculate team points (simplified F1 system)
        points = 0
        for r in results:
            if not r.dnfs:
                points += max(0, 11 - r.position)  # 1st=10, 10th=1

        # Random race events
        if rng.random() < 0.15:
            race_events.append(f"Safety Car deployed on lap {rng.randint(5, race_length - 5)}")
        if rng.random() < 0.10:
            race_events.append(f"Track limit warnings issued to multiple drivers")

        return RaceResult(
            team_id=team.id,
            season=season,
            race_number=race_number,
            track_name=track,
            weather=weather,
            driver_1_result=results[0] if len(results) > 0 else None,
            driver_2_result=results[1] if len(results) > 1 else None,
            team_points=points,
            race_events=race_events,
        )

    def _calc_qualifying_bonus(self, driver: Driver, weather: Weather) -> int:
        """Calculate time bonus from driver stats for qualifying."""
        if weather != Weather.DRY:
            weights = {
                "qualifying_pace": 0.30,
                "speed": 0.25,
                "consistency": 0.15,
                "mental_strength": 0.10,
                "wet_performance": 0.20,
            }
        else:
            weights = {
                "qualifying_pace": 0.35,
                "speed": 0.30,
                "consistency": 0.15,
                "mental_strength": 0.10,
                "wet_performance": 0.00,
                "racecraft": 0.10,
            }

        weighted_score = sum(
            getattr(driver.attributes, attr) * weight
            for attr, weight in weights.items()
        )
        return int(weighted_score * 50)  # Max ~5000ms

    def _calc_race_pace(self, driver: Driver, team: Team, weather: Weather) -> int:
        """Calculate average lap pace for a race."""
        if weather != Weather.DRY:
            weights = {
                "speed": 0.25,
                "consistency": 0.20,
                "racecraft": 0.20,
                "overtaking": 0.10,
                "tyre_management": 0.10,
                "wet_performance": 0.15,
            }
        else:
            weights = {
                "speed": 0.25,
                "consistency": 0.20,
                "racecraft": 0.20,
                "overtaking": 0.15,
                "tyre_management": 0.10,
                "wet_performance": 0.00,
                "mental_strength": 0.10,
            }

        weighted_score = sum(
            getattr(driver.attributes, attr) * weight
            for attr, weight in weights.items()
        )

        team_bonus = team.performance_rating * 15  # Max 1500ms

        base = 95000
        skill_bonus = int(weighted_score * 50)  # Max ~5000ms
        lap_time = base - skill_bonus - team_bonus

        return max(65000, int(lap_time))


class QualifierSystem:
    """Manages qualifier sessions and result tracking."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine

    def run_qualifier(self, team: Team, season: int, race_number: int,
                      weather: Optional[Weather] = None) -> QualifierResult:
        """Run a full qualifier session for a team's 3 drivers."""
        if weather is None:
            weather = WeatherSystem.roll_weather(season, race_number)

        drivers = [
            team.main_driver_1,
            team.main_driver_2,
            team.reserve_driver,
        ]

        times = []
        for d in drivers:
            if d is None:
                # If driver slot empty, use a penalty time
                league = League(f"F{team.league}")
                times.append(league.base_lap_time_ms + 5000)
            else:
                lap = self.engine.simulate_qualifier_lap(
                    d, team, season, race_number, weather
                )
                times.append(lap)

        avg = int(sum(times) / len(times))

        return QualifierResult(
            id=str(uuid.uuid4()),
            team_id=team.id,
            league=team.league,
            season=season,
            race_number=race_number,
            driver_1_time_ms=times[0],
            driver_2_time_ms=times[1],
            driver_3_time_ms=times[2],
            average_time_ms=avg,
            was_auto=False,
        )

    @staticmethod
    def get_standard_time(league: int, median_time_ms: int) -> int:
        """Calculate standard time for AFK teams."""
        league_enum = League(f"F{league}")
        return median_time_ms + league_enum.qualifier_penalty_ms
