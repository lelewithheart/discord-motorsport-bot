"""
Training system for the Motorsport Universe.
Each team gets 20 training laps per day, split between drivers.
Each lap earns 2 R&D points.
"""
from __future__ import annotations
import random
from typing import Optional
from motorsport.data.models import SetupModel, TrackModel
from motorsport.systems.setup import SetupCalculator

# Default track stats when no track is available
_DEFAULT_TRACK = {
    "req_speed": 0.5,
    "req_acceleration": 0.5,
    "req_downforce": 0.5,
    "req_braking": 0.5,
    "req_tyre_management": 0.5,
}


class TrainingEngine:
    """Simulates training laps and calculates performance."""

    MAX_TRAINING_LAPS_PER_DAY = 20
    RND_POINTS_PER_LAP = 2  # 2 R&D points per training lap

    @staticmethod
    def _get_track_reqs(track: TrackModel | None) -> dict:
        """Get track requirements dict, with defaults if track is None."""
        if track is None:
            return _DEFAULT_TRACK
        return {
            "req_speed": getattr(track, "req_speed", 0.5),
            "req_acceleration": getattr(track, "req_acceleration", 0.5),
            "req_downforce": getattr(track, "req_downforce", 0.5),
            "req_braking": getattr(track, "req_braking", 0.5),
            "req_tyre_management": getattr(track, "req_tyre_management", 0.5),
        }

    @staticmethod
    def simulate_lap(driver_attrs: dict, setup: SetupModel,
                     track: TrackModel | None = None,
                     weather: str = "dry", personality: str = "calm") -> int:
        """
        Simulate one lap, return time in milliseconds.

        Driver stats mapped to track requirements:
          speed          → req_speed
          qualifying_pace → req_acceleration  (acceleration feel)
          consistency    → req_downforce      (cornering feel)
          mental_strength → req_braking
          tyre_management → req_tyre_management
        """
        track_reqs = TrainingEngine._get_track_reqs(track)

        # Get setup bonuses
        bonuses = SetupCalculator.calculate_stat_bonuses(setup, track)

        # Effective stats based on track requirements
        effective_speed = driver_attrs.get("speed", 50) * track_reqs["req_speed"] * bonuses.get("speed", 1.0)
        effective_accel = driver_attrs.get("qualifying_pace", 50) * track_reqs["req_acceleration"] * bonuses.get("acceleration", 1.0)
        effective_downforce = driver_attrs.get("consistency", 50) * track_reqs["req_downforce"] * bonuses.get("downforce", 1.0)
        effective_braking = driver_attrs.get("mental_strength", 50) * track_reqs["req_braking"] * bonuses.get("braking", 1.0)
        effective_tyre = driver_attrs.get("tyre_management", 50) * track_reqs["req_tyre_management"] * bonuses.get("tyre_management", 1.0)

        # Driver happiness with setup
        happiness = SetupCalculator.calculate_driver_happiness(setup, personality)

        # Base lap time
        base_ms = int(60000 + (100 - track_reqs["req_speed"] * 30))

        # Performance factor (higher effective stats = lower time = faster)
        perf_factor = (effective_speed + effective_accel + effective_downforce
                       + effective_braking + effective_tyre) / 250

        # Apply performance (negative = faster)
        perf_bonus = int((50 - min(99, perf_factor * 50)) * 100)

        # Happiness bonus/penalty
        happiness_bonus = int((happiness - 0.5) * 500)

        # Random variation
        variation = random.randint(-500, 500)

        # Weather penalty
        weather_penalty = 0
        if weather == "rain":
            wet_mult = (1.0 - driver_attrs.get("wet_performance", 50) / 200)
            weather_penalty = int(3000 * wet_mult)

        lap_time = base_ms + perf_bonus + happiness_bonus + variation + weather_penalty
        return max(30000, min(120000, lap_time))

    @staticmethod
    def run_training(driver_attrs: dict, setup: SetupModel,
                     track: TrackModel | None = None,
                     laps: int = 5, weather: str = "dry",
                     personality: str = "calm") -> dict:
        """Run N training laps, return results."""
        laps = max(1, min(20, laps))
        lap_times = []
        for _ in range(laps):
            time_ms = TrainingEngine.simulate_lap(
                driver_attrs, setup, track, weather, personality
            )
            lap_times.append(time_ms)

        return {
            "lap_times": lap_times,
            "best_lap": min(lap_times),
            "avg_lap": sum(lap_times) // len(lap_times),
            "total_laps": laps,
            "rnd_points_earned": laps * TrainingEngine.RND_POINTS_PER_LAP,
        }


# Singleton
training_engine = TrainingEngine()
