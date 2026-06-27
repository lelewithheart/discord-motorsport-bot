"""
Dynamic sponsor generation system for the Discord Motorsport Universe.
"""
from __future__ import annotations
import random
import uuid
from decimal import Decimal
from typing import Optional
from motorsport.models import Sponsor, SponsorType, Team


SPONSOR_NAMES_BY_TYPE = {
    SponsorType.LOCAL: [
        "City Motors", "Downtown Garage", "Harbor Racing", "Alpine Parts",
        "Metro Tyres", "Bay Auto", "River City Petrol", "Coastal Mechanics",
        "Valley Speed Shop", "Sunset Lubricants", "Nordic Brakes",
    ],
    SponsorType.REGIONAL: [
        "EuroWheels", "Nordic Automotive", "Iberian Racing", "Atlantic Oils",
        "PanEuropean Parts", "Scandinavian Motors", "Mediterranean Tyres",
        "Continental Fuel", "Alpine Racing Tech", "Danube Lubricants",
    ],
    SponsorType.GLOBAL: [
        "GlobalOil Corp", "WorldWide Tyres", "International Motors",
        "United Fuel Systems", "Orbital Racing", "Planetary Autos",
        "Fusion Energy Drink", "Titanium Brake Systems", "Vector Lubricants",
        "Quantum Racing Technologies", "Apex Financial Group",
    ],
    SponsorType.MEGA: [
        "Titans Energy Drink", "Cosmos Petroleum", "Galaxy Insurance",
        "Omega Automotive", "Phoenix Racing Group", "Nebula Technologies",
        "Horizon Air Freight", "Avalanche Sportswear", "Imperial Motors",
    ],
    SponsorType.TITLE: [
        "Apex Racing", "Prime Motorsport", "Vertex Racing",
        "Crown Racing Division", "Supreme Grand Prix", "Royal Racing",
        "Elite Motorsport Group", "Pinnacle Racing", "Summit GP",
    ],
}

SPONSOR_PREFIXES = [
    "Elite", "Prime", "Dynamic", "Premium", "NextGen", "Future",
    "Advanced", "Ultimate", "Pro", "Max", "Rapid", "Swift", "Turbo",
]

SPONSOR_SUFFIXES = [
    "Technologies", "Industries", "Group", "Solutions", "Systems",
    "Racing", "Motorsport", "Engineering", "Dynamics", "Performance",
]


class SponsorGenerator:
    """Generates dynamic sponsors for teams."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate_sponsor(self, team: Team) -> Sponsor:
        """Generate a sponsor appropriate for the given team."""
        # Determine sponsor type
        sponsor_type = self._determine_type(team)

        # Base budget range
        budget_ranges = {
            SponsorType.LOCAL: (500_000, 2_000_000),
            SponsorType.REGIONAL: (2_000_000, 5_000_000),
            SponsorType.GLOBAL: (5_000_000, 10_000_000),
            SponsorType.MEGA: (10_000_000, 20_000_000),
            SponsorType.TITLE: (15_000_000, 30_000_000),
        }

        budget_min, budget_max = budget_ranges[sponsor_type]

        # Performance multiplier
        perf_mult = 0.5 + (team.performance_rating / 200)
        budget = int(self.rng.randint(budget_min, budget_max) * perf_mult)

        # Name
        name = self._generate_name(sponsor_type)

        # Bonus per win/podium
        bonus_per_win = int(budget * 0.05) if sponsor_type.value >= SponsorType.GLOBAL.value else 0
        bonus_per_podium = int(budget * 0.02) if sponsor_type.value >= SponsorType.REGIONAL.value else 0

        return Sponsor(
            id=str(uuid.uuid4()),
            name=name,
            sponsor_type=sponsor_type,
            budget=Decimal(str(budget)),
            contract_seasons=self.rng.randint(1, 3),
            seasons_remaining=self.rng.randint(1, 3),
            min_performance=max(0, team.performance_rating - 20),
            min_league=max(1, team.league - 2),
            driver_nationality_bonus=self.rng.random() < 0.3,
            bonus_per_win=Decimal(str(bonus_per_win)),
            bonus_per_podium=Decimal(str(bonus_per_podium)),
        )

    def _determine_type(self, team: Team) -> SponsorType:
        """Determine appropriate sponsor type for team."""
        league = team.league
        perf = team.performance_rating

        if league <= 2 and perf >= 75:
            weights = {
                SponsorType.LOCAL: 0.0,
                SponsorType.REGIONAL: 0.0,
                SponsorType.GLOBAL: 0.30,
                SponsorType.MEGA: 0.40,
                SponsorType.TITLE: 0.30,
            }
        elif league <= 4 and perf >= 60:
            weights = {
                SponsorType.LOCAL: 0.0,
                SponsorType.REGIONAL: 0.15,
                SponsorType.GLOBAL: 0.40,
                SponsorType.MEGA: 0.30,
                SponsorType.TITLE: 0.15,
            }
        elif league <= 6 and perf >= 45:
            weights = {
                SponsorType.LOCAL: 0.05,
                SponsorType.REGIONAL: 0.30,
                SponsorType.GLOBAL: 0.40,
                SponsorType.MEGA: 0.20,
                SponsorType.TITLE: 0.05,
            }
        elif league <= 8:
            weights = {
                SponsorType.LOCAL: 0.15,
                SponsorType.REGIONAL: 0.40,
                SponsorType.GLOBAL: 0.30,
                SponsorType.MEGA: 0.15,
                SponsorType.TITLE: 0.0,
            }
        else:
            weights = {
                SponsorType.LOCAL: 0.40,
                SponsorType.REGIONAL: 0.35,
                SponsorType.GLOBAL: 0.20,
                SponsorType.MEGA: 0.05,
                SponsorType.TITLE: 0.0,
            }

        return self.rng.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]

    def _generate_name(self, sponsor_type: SponsorType) -> str:
        """Generate a realistic sponsor name."""
        names = SPONSOR_NAMES_BY_TYPE.get(sponsor_type, SPONSOR_NAMES_BY_TYPE[SponsorType.LOCAL])

        if self.rng.random() < 0.6:
            return self.rng.choice(names)
        else:
            prefix = self.rng.choice(SPONSOR_PREFIXES)
            suffix = self.rng.choice(SPONSOR_SUFFIXES)
            return f"{prefix} {suffix}"


class SponsorNegotiator:
    """Handles sponsor contract negotiation."""

    @staticmethod
    def calculate_bonus(sponsor: Sponsor, team: Team, wins: int, podiums: int) -> Decimal:
        """Calculate bonus payout based on results."""
        total = Decimal("0")
        total += sponsor.bonus_per_win * wins
        total += sponsor.bonus_per_podium * podiums
        return total

    @staticmethod
    def nationality_bonus(sponsor: Sponsor, team: Team) -> Decimal:
        """Additional budget if driver matches sponsor region."""
        if not sponsor.driver_nationality_bonus:
            return Decimal("0")
        # Simplified: 15% bonus if any driver nationality matches a target
        return sponsor.budget * Decimal("0.15")
