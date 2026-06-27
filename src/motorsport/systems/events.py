"""
Dynamic world event system for the Discord Motorsport Universe.
Generates random events that affect drivers, teams, and the world.
"""
from __future__ import annotations
import random
import uuid
from typing import Optional
from motorsport.models import Driver, Team, WorldEvent


ALL_ATTRIBUTES = [
    "speed", "consistency", "racecraft", "overtaking",
    "tyre_management", "qualifying_pace", "wet_performance", "mental_strength"
]


class EventEngine:
    """Generates dynamic world events."""

    EVENT_DEFS = {
        "star_development": {
            "chance": 0.05,
            "icon": "⭐⭐",
            "template": "{driver} hat diese Saison einen Sprung gemacht! Alle Attribute +5 bis +10.",
            "apply": lambda driver, rng: {
                attr: min(99, getattr(driver.attributes, attr) + rng.randint(5, 10))
                for attr in ALL_ATTRIBUTES
            },
        },
        "career_ending_injury": {
            "chance": 0.01,
            "icon": "🏥",
            "template": "{driver} hat eine schwere Verletzung erlitten — Karriere beendet.",
            "apply": lambda driver, rng: {"_retire": True},
        },
        "sponsor_bonanza": {
            "chance": 0.03,
            "icon": "💰",
            "template": "Ein Großsponsor wurde auf {driver} aufmerksam! Sponsoreneinnahmen steigen um 30%.",
            "apply": lambda driver, rng: {"_sponsor_mult": 1.3},
        },
        "breakthrough": {
            "chance": 0.03,
            "icon": "💡",
            "template": "{driver} hat einen technischen Durchbruch erzielt! Speed +15.",
            "apply": lambda driver, rng: {"speed": min(99, getattr(driver.attributes, "speed", 50) + 15)},
        },
        "scandal": {
            "chance": 0.02,
            "icon": "📰",
            "template": "Skandal um {driver}! Team-Image leidet, Moral sinkt stark.",
            "apply": lambda driver, rng: {
                "_morale": max(10, driver.morale - 20),
                "_team_perf_drop": -5,
            },
        },
        "mentor_effect": {
            "chance": 0.03,
            "icon": "🎓",
            "template": "{driver} trainiert mit einer Rennlegende — gewaltiger Erfahrungsschub!",
            "apply": lambda driver, rng: {
                attr: min(99, getattr(driver.attributes, attr) + 3)
                for attr in ["racecraft", "mental_strength", "consistency"]
            },
        },
        "contract_drama": {
            "chance": 0.04,
            "icon": "📝",
            "template": "Vertragsstreitigkeiten um {driver}. Team-Moral leidet.",
            "apply": lambda driver, rng: {"_morale": max(10, driver.morale - 10)},
        },
        "fan_favorite": {
            "chance": 0.04,
            "icon": "👑",
            "template": "{driver} wird zum Publikumsliebling! Moral und Sponsoren profitieren.",
            "apply": lambda driver, rng: {
                "_morale": min(100, driver.morale + 10),
                "_sponsor_mult": 1.1,
            },
        },
        "injury_minor": {
            "chance": 0.03,
            "icon": "🤕",
            "template": "{driver} hat eine leichte Verletzung — Form ist beeinträchtigt.",
            "apply": lambda driver, rng: {
                attr: max(10, getattr(driver.attributes, attr) - 3)
                for attr in ["speed", "consistency"]
            },
        },
        "podium_streak": {
            "chance": 0.02,
            "icon": "🏆",
            "template": "{driver} ist in großartiger Form! Podiumsserie beflügelt den Fahrer.",
            "apply": lambda driver, rng: {
                "_morale": min(100, driver.morale + 15),
                "mental_strength": min(99, driver.attributes.mental_strength + 5),
            },
        },
    }

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def roll_events(self, driver: Driver, team: Team,
                    season: int, race_number: int) -> list[WorldEvent]:
        """Roll for events affecting a driver after a race."""
        events = []

        for event_name, event_data in self.EVENT_DEFS.items():
            if self.rng.random() < event_data["chance"]:
                # Calculate effects
                effects = event_data["apply"](driver, self.rng)

                description = event_data["template"].format(
                    driver=driver.full_name,
                    team=team.name,
                )

                event = WorldEvent(
                    id=str(uuid.uuid4()),
                    event_type=event_name,
                    description=f"{event_data['icon']} {description}",
                    season=season,
                    race_number=race_number,
                    effects=effects,
                    target_team_id=team.id,
                    target_driver_id=driver.id,
                )
                events.append(event)

        return events

    def apply_event(self, driver: Driver, team: Team, event: WorldEvent) -> tuple[Driver, Team]:
        """Apply event effects to driver and team."""
        effects = event.effects or {}

        for attr, value in effects.items():
            if attr.startswith("_"):
                if attr == "_retire":
                    driver.is_retired = True
                    driver.retirement_season = event.season
                elif attr == "_morale":
                    driver.morale = value
                elif attr == "_sponsor_mult":
                    pass  # handled by sponsor system
                elif attr == "_team_perf_drop":
                    team.performance_rating = max(0, team.performance_rating + value)
            elif hasattr(driver.attributes, attr):
                current = getattr(driver.attributes, attr)
                setattr(driver.attributes, attr, max(10, min(99, int(value))))

        return driver, team
