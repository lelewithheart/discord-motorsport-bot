"""
Car setup system for the Motorsport Universe.
Setup parameters (1-20 scale) affect car performance on different tracks.
"""
from __future__ import annotations
from typing import Optional
from motorsport.data.models import SetupModel, TrackModel

# Driver preferences: each personality likes different setup biases
DRIVER_SETUP_PREFERENCES = {
    "calm": {"suspension_bias": 5, "wing_bias": 0},       # Soft, balanced
    "aggressive": {"suspension_bias": 15, "wing_bias": 15},  # Hard, high downforce
    "inconsistent": {"suspension_bias": 10, "wing_bias": 5},
    "strategic": {"suspension_bias": 7, "wing_bias": 10},  # Balanced
    "clutch": {"suspension_bias": 12, "wing_bias": 12},    # Slight edge
}


class SetupCalculator:
    """
    Calculates how setup affects performance.
    
    Setup→Stat mapping:
    - front_wing: +downforce, -speed
    - rear_wing: +stability, -speed
    - suspension: soft=+tyre_management, hard=+responsiveness
    - gear_ratio: short=+acceleration, long=+speed  
    - tire_compound: soft=+grip, hard=+durability
    """

    @staticmethod
    def calculate_stat_bonuses(setup: SetupModel, track: TrackModel) -> dict[str, float]:
        """
        Calculate how the setup modifies driver stats for this track.
        Returns multipliers like {"speed": 1.05, "downforce": 1.10}
        """
        bonuses = {
            "speed": 1.0,
            "acceleration": 1.0,
            "downforce": 1.0,
            "braking": 1.0,
            "tyre_management": 1.0,
        }
        
        # Front wing: more wing = more downforce, less speed
        wing_factor = (setup.front_wing - 10) * 0.02  # -0.2 to +0.2
        bonuses["downforce"] += wing_factor * 0.5
        bonuses["speed"] -= wing_factor * 0.3
        
        # Rear wing: affects stability and speed
        rear_factor = (setup.rear_wing - 10) * 0.02
        bonuses["downforce"] += rear_factor * 0.3
        bonuses["speed"] -= rear_factor * 0.4
        
        # Suspension: soft = better tyre management, hard = better responsiveness
        susp_factor = (setup.suspension - 10) * 0.015
        bonuses["tyre_management"] -= susp_factor * 0.3  # soft = better wear
        bonuses["braking"] += susp_factor * 0.4  # hard = better braking
        
        # Gear ratio: short = acceleration, long = top speed
        gear_factor = (setup.gear_ratio - 10) * 0.02
        bonuses["acceleration"] -= gear_factor * 0.4  # short gear = better accel
        bonuses["speed"] += gear_factor * 0.3  # long gear = better top speed
        
        # Tire compound: soft = grip, hard = durability
        tire_factor = (setup.tire_compound - 10) * 0.015
        bonuses["acceleration"] -= tire_factor * 0.2  # soft = better accel
        bonuses["tyre_management"] += tire_factor * 0.3  # hard = better wear
        
        return bonuses

    @staticmethod
    def calculate_driver_happiness(setup: SetupModel, personality: str) -> float:
        """0.0-1.0 How much the driver likes this setup based on personality."""
        prefs = DRIVER_SETUP_PREFERENCES.get(personality, DRIVER_SETUP_PREFERENCES["calm"])
        
        # How close is setup to driver's preferred values
        susp_diff = abs(setup.suspension - prefs["suspension_bias"])
        wing_diff = abs(setup.front_wing - prefs["wing_bias"]) + abs(setup.rear_wing - prefs["wing_bias"])
        
        # Lower diff = higher happiness
        happiness = max(0.0, 1.0 - (susp_diff + wing_diff * 0.5) / 30)
        return happiness

    @staticmethod
    def recommend_setup(track: TrackModel) -> dict[str, int]:
        """Recommend a basic setup based on track characteristics."""
        setup = {"front_wing": 10, "rear_wing": 10, "suspension": 10,
                 "gear_ratio": 10, "tire_compound": 10}
        
        # High downforce tracks need more wing
        if track.req_downforce > 0.7:
            setup["front_wing"] = 16
            setup["rear_wing"] = 15
        elif track.req_downforce < 0.4:
            setup["front_wing"] = 4
            setup["rear_wing"] = 5
        
        # High accel tracks need short gears
        if track.req_acceleration > 0.7:
            setup["gear_ratio"] = 4
        elif track.req_speed > 0.7:
            setup["gear_ratio"] = 16
        
        # High braking tracks need harder suspension
        if track.req_braking > 0.7:
            setup["suspension"] = 15
        elif track.req_tyre_management > 0.7:
            setup["suspension"] = 5
        
        # Tyre management tracks need harder compound
        if track.req_tyre_management > 0.7:
            setup["tire_compound"] = 15
        elif track.req_braking > 0.5 and track.req_acceleration > 0.5:
            setup["tire_compound"] = 5  # Soft for grip
        
        return setup
    
    @staticmethod
    def setup_to_dict(setup: SetupModel) -> dict:
        return {
            "front_wing": setup.front_wing,
            "rear_wing": setup.rear_wing,
            "suspension": setup.suspension,
            "gear_ratio": setup.gear_ratio,
            "tire_compound": setup.tire_compound,
        }


# For convenience
setup_calculator = SetupCalculator()
