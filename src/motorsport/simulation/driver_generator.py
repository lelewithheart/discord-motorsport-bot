"""
Procedural driver generator with attributes, personality, and development.
"""
from __future__ import annotations
import random
import uuid
from typing import Optional
from motorsport.models import (
    Driver, DriverAttributes, HiddenStats, Personality,
    PERSONALITY_MODIFIERS,
)
from motorsport.simulation.name_generator import NameGenerator

ALL_ATTRIBUTES_LIST = [
    "speed", "consistency", "racecraft", "overtaking",
    "tyre_management", "qualifying_pace", "wet_performance", "mental_strength"
]

# Age development multipliers
AGE_GROWTH_MULT = {
    "rookie": 1.5,
    "developing": 1.2,
    "peak": 1.0,
    "late_peak": 0.7,
    "veteran": 0.3,
    "decline": 0.0,
}

# Attribute decay in decline phase (per race)
DECLINE_RATE_BY_AGE = {
    31: 0.05, 32: 0.08, 33: 0.12, 34: 0.15, 35: 0.20,
    36: 0.30, 37: 0.40, 38: 0.50, 39: 0.60, 40: 0.70,
    41: 0.80, 42: 0.90, 43: 1.00, 44: 1.10, 45: 1.20,
}


class DriverGenerator:
    """Generates procedural racing drivers with realistic attributes."""

    def __init__(self, seed: Optional[int] = None):
        self.name_gen = NameGenerator(seed)
        self.rng = random.Random(seed)

    def generate_driver(self, age: Optional[int] = None,
                        potential_bias: float = 0.0,
                        region_bias: Optional[str] = None,
                        is_academy: bool = False) -> Driver:
        """Generate a complete driver with name, attributes, personality.
        
        Args:
            age: Specific age, or None for random
            potential_bias: 0.0 (random) to 1.0 (always high potential)
            region_bias: Optional region to bias names from
            is_academy: If True, lower base attributes
        """
        # Name
        if region_bias and self.rng.random() < 0.6:
            sub = self.name_gen.pick_sub_region_from(region_bias)
        else:
            _, sub = self.name_gen._pick_region()
        name = self.name_gen.generate_name(sub)

        # Age
        if age is None:
            if is_academy:
                age = self.rng.randint(16, 19)
            else:
                age = self.rng.randint(16, 38)

        # Potential
        if is_academy:
            base_potential = self.rng.randint(40, 90)
        else:
            base_potential = self.rng.randint(45, 97)

        # Apply bias toward high potential
        if potential_bias > 0:
            boost = int(potential_bias * 20)
            base_potential = min(99, base_potential + boost)

        # Hidden stats
        hidden = HiddenStats(
            potential=base_potential,
            growth_rate=round(self.rng.uniform(0.3, 1.5), 2),
            aggression=self.rng.randint(20, 95),
            risk_taking=self.rng.randint(15, 95),
            pressure_handling=self.rng.randint(25, 95),
        )

        # Base attributes scaled by potential
        attrs = {}
        for attr_name in ALL_ATTRIBUTES_LIST:
            if is_academy:
                base = self.rng.randint(25, 55)
            else:
                base = self.rng.randint(30, 70)
            # Scale by potential
            potential_scale = 1 + (base_potential - 50) / 100
            attrs[attr_name] = min(99, max(10, int(base * potential_scale)))

        attributes = DriverAttributes(**attrs)

        # Personality
        personality = self.rng.choice(list(Personality))

        driver = Driver(
            id=str(uuid.uuid4()),
            first_name=name["first_name"],
            last_name=name["last_name"],
            nationality=name["nationality"],
            age=age,
            attributes=attributes,
            hidden=hidden,
            personality=personality,
            is_academy=is_academy,
            morale=self.rng.randint(40, 90),
        )

        # Apply personality modifiers
        driver.apply_personality_modifiers()

        return driver

    def generate_multiple(self, count: int, **kwargs) -> list[Driver]:
        """Generate multiple drivers."""
        return [self.generate_driver(**kwargs) for _ in range(count)]

    def set_seed(self, seed: int):
        self.rng = random.Random(seed)
        self.name_gen.set_seed(seed)


class DriverDevelopment:
    """Handles driver attribute progression over time."""

    @staticmethod
    def develop(driver: Driver, team_performance: int,
                race_result_score: float,  # 0.0-1.0
                training_level: int = 1) -> Driver:
        """Progress driver attributes after a race.
        
        Args:
            driver: The driver to develop
            team_performance: 0-100
            race_result_score: 0.0 (last) to 1.0 (win)
            training_level: 1-5
        """
        if driver.is_retired:
            return driver

        age_group = driver.age_group

        # Decline phase: forced decay
        if age_group == "decline":
            decay = DECLINE_RATE_BY_AGE.get(driver.age, 0.5)
            for attr in ALL_ATTRIBUTES_LIST:
                current = getattr(driver.attributes, attr)
                new_val = max(10, current - decay * self.rng())
                setattr(driver.attributes, attr, int(new_val))
            return driver

        # Growth
        growth_mult = AGE_GROWTH_MULT.get(age_group, 1.0)
        if growth_mult == 0:
            return driver

        base_growth = driver.hidden.growth_rate * growth_mult * 0.15
        team_factor = team_performance / 100
        result_factor = race_result_score

        for attr in ALL_ATTRIBUTES_LIST:
            current = getattr(driver.attributes, attr)

            # Potential cap: can exceed potential slightly
            max_possible = driver.hidden.potential * (1 + (100 - driver.hidden.potential) / 200)
            if current >= max_possible:
                continue  # already at potential

            gain = base_growth * team_factor * (1 + result_factor)
            gain += training_level * 0.08

            new_val = min(max_possible, current + gain)
            setattr(driver.attributes, attr, int(new_val))

        # Veteran: slight decay alongside growth
        if age_group == "veteran":
            decay = 0.08
            for attr in ALL_ATTRIBUTES_LIST:
                current = getattr(driver.attributes, attr)
                new_val = max(10, current - decay)
                setattr(driver.attributes, attr, int(new_val))

        # Morale changes based on result
        if race_result_score > 0.7:
            driver.morale = min(100, driver.morale + 3)
        elif race_result_score < 0.3:
            driver.morale = max(10, driver.morale - 3)

        return driver

    @staticmethod
    def seasonal_decay(driver: Driver) -> Driver:
        """Apply end-of-season decay for older drivers."""
        if driver.age >= 31:
            decay = (driver.age - 30) * 0.3
            for attr in ALL_ATTRIBUTES_LIST:
                current = getattr(driver.attributes, attr)
                new_val = max(10, current - decay)
                setattr(driver.attributes, attr, int(new_val))

        # Age up
        driver.age += 1

        # Check retirement
        if driver.age >= 40:
            driver.is_retired = True
        elif driver.age >= 35 and driver.hidden.potential < 60:
            # Lower potential drivers may retire earlier
            if self.rng() < 0.3:
                driver.is_retired = True

        return driver

    @staticmethod
    def rng() -> float:
        return random.random()
