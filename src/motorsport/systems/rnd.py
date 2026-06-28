"""
Research & Development system for the Motorsport Universe.
Points earned from laps (training, quali, race) can be spent on component upgrades.
Each component level adds stat bonuses to the car.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


# R&D component definitions
RND_COMPONENTS = {
    "engine": {
        "name": "Motor",
        "max_level": 10,
        "costs": [100, 250, 500, 800, 1200, 1700, 2300, 3000, 4000, 5000],
        "effects": {"speed": 2, "acceleration": 1},
    },
    "front_wing": {
        "name": "Frontflügel",
        "max_level": 10,
        "costs": [80, 200, 400, 650, 950, 1300, 1800, 2400, 3200, 4000],
        "effects": {"downforce": 3, "speed": -0.5},
    },
    "rear_wing": {
        "name": "Heckflügel",
        "max_level": 10,
        "costs": [80, 200, 400, 650, 950, 1300, 1800, 2400, 3200, 4000],
        "effects": {"downforce": 2, "stability": 3},
    },
    "chassis": {
        "name": "Chassis",
        "max_level": 10,
        "costs": [120, 300, 550, 900, 1300, 1800, 2500, 3200, 4200, 5500],
        "effects": {"braking": 2, "tyre_management": 1, "speed": 1},
    },
    "brakes": {
        "name": "Bremsen",
        "max_level": 8,
        "costs": [60, 150, 300, 500, 750, 1000, 1400, 1800],
        "effects": {"braking": 4},
    },
    "gearbox": {
        "name": "Getriebe",
        "max_level": 8,
        "costs": [70, 180, 350, 550, 800, 1100, 1500, 2000],
        "effects": {"acceleration": 3, "speed": 1},
    },
    "suspension": {
        "name": "Aufhängung",
        "max_level": 8,
        "costs": [50, 120, 250, 450, 700, 1000, 1400, 1800],
        "effects": {"tyre_management": 2, "braking": 1},
    },
}

# Race bonuses: R&D points earned per race
RND_RACE_BONUS = 5  # bonus R&D for completing a race
RND_QUALI_BONUS = 3  # bonus for completing quali


class RndManager:
    """Manages R&D point tracking and upgrades."""

    @staticmethod
    def get_upgrade_cost(component: str, current_level: int) -> Optional[int]:
        """Get R&D points needed for next level. Returns None if max level."""
        comp = RND_COMPONENTS.get(component)
        if not comp:
            return None
        costs = comp["costs"]
        if current_level >= len(costs):
            return None
        return costs[current_level]

    @staticmethod
    def get_component_info(component: str) -> Optional[dict]:
        """Get component definition."""
        return RND_COMPONENTS.get(component)

    @staticmethod
    def calculate_stat_bonuses(upgrades: list) -> dict[str, float]:
        """
        Calculate total stat bonuses from all R&D upgrades.

        Args:
            upgrades: list of objects with .component and .level attributes
                      (e.g. RndUpgradeModel instances)

        Returns:
            Dict of stat name -> bonus amount (e.g. {"speed": 8, "acceleration": 4})
        """
        bonuses = {}
        for upgrade in upgrades:
            comp = RND_COMPONENTS.get(upgrade.component)
            if not comp:
                continue
            for stat, per_level in comp["effects"].items():
                current = bonuses.get(stat, 0.0)
                # Level 1 gives no bonus yet, level 2 gives per_level, etc.
                level_bonus = (upgrade.level - 1) * per_level
                bonuses[stat] = current + level_bonus
        return bonuses

    @staticmethod
    def get_max_level(component: str) -> int:
        """Get max level for a component."""
        comp = RND_COMPONENTS.get(component)
        return comp["max_level"] if comp else 0

    @staticmethod
    def all_components() -> list[dict]:
        """Return list of all component info dicts with name, key, max_level."""
        return [
            {"key": k, **v}
            for k, v in RND_COMPONENTS.items()
        ]
