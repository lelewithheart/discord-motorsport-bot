"""
Academy system for driver development pipeline.
Handles yearly driver drops and scouting.
"""
from __future__ import annotations
import random
from decimal import Decimal
from typing import Optional
from motorsport.models import Driver, Team, Scout
from motorsport.simulation.driver_generator import DriverGenerator


class AcademySystem:
    """Manages the academy driver pipeline."""

    def __init__(self, seed: Optional[int] = None):
        self.generator = DriverGenerator(seed)
        self.rng = random.Random(seed)

    def generate_academy_drop(
        self,
        team: Team,
        scout: Optional[Scout] = None,
        season: int = 1,
    ) -> list[Driver]:
        """Generate new academy drivers for a team at season end.
        
        Args:
            team: The team receiving academy drivers
            scout: Optional scout for bonuses
            season: Current season
            
        Returns:
            List of new academy drivers
        """
        # Base number of drivers
        base_count = 5
        if scout:
            base_count += scout.extra_drivers

        # Region bias from scout
        region_bias = scout.region if scout else None

        # Potential bias from scout
        potential_bias = 0.0
        if scout:
            potential_bias = min(1.0, scout.level * 0.15)

        drivers = []
        for _ in range(base_count):
            # Some may be higher quality
            if self.rng.random() < potential_bias:
                bias = potential_bias
            else:
                bias = self.rng.random() * 0.3  # still some variance

            d = self.generator.generate_driver(
                age=self.rng.randint(16, 19),
                potential_bias=bias,
                region_bias=region_bias,
                is_academy=True,
            )
            drivers.append(d)

        # Sort by potential (best first)
        drivers.sort(key=lambda d: d.hidden.potential, reverse=True)

        return drivers

    @staticmethod
    def hire_scout(team_id: str, level: int = 1,
                   region: Optional[str] = None) -> Scout:
        """Create a new scout for a team."""
        return Scout(
            id=f"scout_{team_id}_{level}",
            team_id=team_id,
            level=level,
            region=region,
            cost_per_season=Decimal(str(100_000 * level)),
        )
