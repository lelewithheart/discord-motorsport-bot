"""
Season scheduler and game state machine for the Discord Motorsport Universe.
Manages the season lifecycle and coordinates all systems.
"""
from __future__ import annotations
import random
from decimal import Decimal
from typing import Optional, Callable
from motorsport.models import (
    Team, Driver, SeasonPhase, SeasonState, League, Weather,
    RaceResult, QualifierResult, TeamRank, WorldEvent,
)
from motorsport.simulation.engine import (
    SimulationEngine, QualifierSystem, WeatherSystem
)
from motorsport.simulation.ranking import RankingCalculator, PromotionResult
from motorsport.simulation.driver_generator import DriverDevelopment, ALL_ATTRIBUTES_LIST
from motorsport.systems.sponsors import SponsorGenerator
from motorsport.systems.academy import AcademySystem
from motorsport.systems.events import EventEngine


class SeasonManager:
    """
    Manages the complete season lifecycle for a league.
    Coordinates simulation, ranking, development, and events.
    """

    def __init__(self, universe_id: str = "default"):
        self.universe_id = universe_id
        self.engine = SimulationEngine(universe_id)
        self.qualifier_system = QualifierSystem(self.engine)
        self.ranking = RankingCalculator()
        self.driver_dev = DriverDevelopment()
        self.sponsor_gen = SponsorGenerator()
        self.academy = AcademySystem()
        self.events = EventEngine()

        # Callbacks for external notification (Discord bot)
        self._on_race: Optional[Callable] = None
        self._on_qualifier: Optional[Callable] = None
        self._on_season_end: Optional[Callable] = None

    def set_callbacks(self, on_race=None, on_qualifier=None, on_season_end=None):
        self._on_race = on_race
        self._on_qualifier = on_qualifier
        self._on_season_end = on_season_end

    # ─── Pre-Season ───────────────────────────────────────────────────────

    def run_pre_season(self, team: Team, season: int) -> dict:
        """Run pre-season preparations for a team."""
        results = {
            "team_id": team.id,
            "season": season,
            "actions": [],
        }

        # Generate sponsor if none
        if not team.sponsor_income or team.sponsor_income == 0:
            sponsor = self.sponsor_gen.generate_sponsor(team)
            team.sponsor_income = sponsor.budget
            results["actions"].append({
                "type": "sponsor_signed",
                "name": sponsor.name,
                "budget": float(sponsor.budget),
            })

        # Reset season stats
        team.wins = 0
        team.podiums = 0
        team.season_points = 0
        team.total_qualifier_time_ms = 0
        team.qualifier_count = 0
        team.current_race = 0
        team.active_season = season

        # Apply some development to all drivers
        for driver in team.drivers:
            self.driver_dev.develop(driver, team.performance_rating, 0.5, 1)

        # Recalculate team performance
        team.recalculate_performance()

        results["team"] = team
        return results

    # ─── Race ──────────────────────────────────────────────────────────────

    def run_race(self, team: Team, season: int,
                 race_number: int) -> RaceResult:
        """Run a full race + driver development cycle."""
        team.current_race = race_number

        # Simulate race
        result = self.engine.simulate_race(team, season, race_number)

        # Update team stats
        if result.team_points > 0:
            if result.driver_1_result and result.driver_1_result.position == 1:
                team.wins += 1
            if result.driver_1_result and result.driver_1_result.position <= 3:
                team.podiums += 1
            if result.driver_2_result and result.driver_2_result.position <= 3:
                team.podiums += 1

        team.season_points += result.team_points

        # Driver development
        for i, driver in enumerate([team.main_driver_1, team.main_driver_2]):
            if driver is None:
                continue
            race_result = result.driver_1_result if i == 0 else result.driver_2_result
            if race_result and not race_result.dnfs:
                score = max(0, 1.0 - (race_result.position - 1) * 0.1)
                self.driver_dev.develop(driver, team.performance_rating, score)
                driver.races_driven += 1

        # Roll for events
        for driver in [team.main_driver_1, team.main_driver_2]:
            if driver:
                events = self.events.roll_events(driver, team, season, race_number)
                for event in events:
                    self.events.apply_event(driver, team, event)
                result.race_events.extend([e.description for e in events])

        # Recalculate team performance
        team.recalculate_performance()

        # Notify
        if self._on_race:
            self._on_race(result)

        return result

    # ─── Qualifier ─────────────────────────────────────────────────────────

    def run_qualifier(self, team: Team, season: int,
                      race_number: int) -> QualifierResult:
        """Run a qualifier session for a team."""
        weather = WeatherSystem.roll_weather(season, race_number)
        result = self.qualifier_system.run_qualifier(
            team, season, race_number, weather
        )

        # Update team stats
        team.total_qualifier_time_ms += result.average_time_ms
        team.qualifier_count += 1
        team.afk_streak = 0  # Participated

        if self._on_qualifier:
            self._on_qualifier(result)

        return result

    def apply_standard_time(self, team: Team, season: int,
                             race_number: int,
                             league_median: int) -> QualifierResult:
        """Apply standard time for AFK team."""
        standard = QualifierSystem.get_standard_time(team.league, league_median)
        team.afk_streak += 1

        from motorsport.models import QualifierResult
        import uuid
        result = QualifierResult(
            id=str(uuid.uuid4()),
            team_id=team.id,
            league=team.league,
            season=season,
            race_number=race_number,
            driver_1_time_ms=standard,
            driver_2_time_ms=standard,
            driver_3_time_ms=standard,
            average_time_ms=standard,
            was_auto=True,
        )

        team.total_qualifier_time_ms += standard
        team.qualifier_count += 1

        return result

    # ─── Post-Season ──────────────────────────────────────────────────────

    def run_post_season(
        self,
        league: int,
        season: int,
        teams: list[Team],
        qualifiers: list[QualifierResult],
    ) -> dict:
        """Run post-season processing for a league."""
        results = {
            "league": league,
            "season": season,
            "rankings": [],
            "promotion": None,
            "retirements": [],
            "academy_drivers": [],
        }

        # Calculate ranking
        team_names = {t.id: t.name for t in teams}
        rankings = self.ranking.calculate_season_ranking(qualifiers, team_names)
        results["rankings"] = rankings

        # Calculate promotion/relegation
        promotion = self.ranking.calculate_promotion_relegation(league, rankings)
        results["promotion"] = promotion

        # Apply relegation penalties
        for team in teams:
            if team.id in promotion.relegations:
                # 50% budget penalty for relegated teams
                team.budget = team.budget * Decimal("0.50")
                team.league = min(10, team.league + 1)

            if team.id in promotion.promotions:
                team.league = max(1, team.league - 1)

        # Driver aging and retirement
        for team in teams:
            for driver in team.drivers:
                if not driver.is_retired:
                    driver.age += 1
                    # Seasonal decay for older drivers
                    if driver.age >= 31:
                        decay = (driver.age - 30) * 0.3
                        for attr in ALL_ATTRIBUTES_LIST:
                            current = getattr(driver.attributes, attr)
                            setattr(driver.attributes, attr, max(10, current - decay))
                    # Check retirement
                    if driver.age >= 40:
                        driver.is_retired = True
                        driver.retirement_season = season
                        results["retirements"].append(driver.full_name)
                    elif driver.age >= 35 and driver.hidden.potential < 60:
                        if random.random() < 0.3:
                            driver.is_retired = True
                            driver.retirement_season = season
                            results["retirements"].append(driver.full_name)

        # Academy drops
        for team in teams:
            if team.is_premium or random.random() < 0.5:
                new_drivers = self.academy.generate_academy_drop(
                    team, season=season
                )
                # Best academy driver gets a slot if reserve is empty
                if new_drivers and team.reserve_driver is None:
                    new_drivers[0].is_academy = False
                    new_drivers[0].slot = 3
                    team.reserve_driver = new_drivers[0]
                results["academy_drivers"].extend(
                    [d.full_name for d in new_drivers[:2]]
                )

        # Budget updates
        for team in teams:
            # Prize money
            for rank in rankings:
                if rank.team_id == team.id:
                    prize = max(0, (11 - rank.rank) * 200_000)
                    team.prize_money = Decimal(str(prize))
                    team.budget += Decimal(str(prize))
                    break

            # Sponsor income
            if team.sponsor_income:
                team.budget += team.sponsor_income

            # Driver salaries (simplified)
            for driver in team.drivers:
                salary = int(driver.attributes.overall() * 20000)
                team.salary_costs = Decimal(str(salary))
                team.budget -= Decimal(str(salary))

        results["teams"] = teams

        if self._on_season_end:
            self._on_season_end(results)

        return results
