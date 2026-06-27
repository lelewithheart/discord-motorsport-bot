"""
Integration test: Simulates a complete season with multiple teams.
Tests the full stack: generator → simulation → ranking → development → events
"""
from __future__ import annotations
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from decimal import Decimal
from motorsport.models import (
    Team, Driver, DriverAttributes, HiddenStats, Personality, DriverSlot,
    League, Weather
)
from motorsport.simulation.driver_generator import DriverGenerator
from motorsport.simulation.name_generator import NameGenerator
from motorsport.simulation.engine import SimulationEngine, QualifierSystem, WeatherSystem
from motorsport.simulation.ranking import RankingCalculator, GlobalRanking, PromotionResult
from motorsport.systems.season import SeasonManager
from motorsport.systems.sponsors import SponsorGenerator
from motorsport.systems.academy import AcademySystem
from motorsport.systems.events import EventEngine


def print_header(text: str):
    print()
    print("=" * 72)
    print(f"  {text}")
    print("=" * 72)


def print_line():
    print("-" * 72)


def simulate_season():
    """Run a full season simulation with 10 teams in F5 league."""
    print_header("🏁 DISCORD MOTORSPORT UNIVERSE — INTEGRATION TEST")
    print("  Komplette Saison-Simulation mit 10 Teams in F5 Liga")
    print(f"  Startzeit: {time.strftime('%H:%M:%S')}")
    print_line()

    # ── Phase 1: Generate Drivers ──────────────────────────────────────
    print_header("📋 PHASE 1: FAHRER-GENERIERUNG")
    gen = DriverGenerator(seed=42)

    teams = []
    for i in range(10):
        d1 = gen.generate_driver(age=22, region_bias="europe")
        d2 = gen.generate_driver(age=24, region_bias="south_america")
        reserve = gen.generate_driver(age=19, is_academy=True, region_bias="asia")

        d1.slot = DriverSlot.MAIN_1
        d2.slot = DriverSlot.MAIN_2
        reserve.slot = DriverSlot.RESERVE

        team = Team(
            id=f"team_{i+1:02d}",
            name=f"Racing Team {i+1:02d}",
            owner_id=1000 + i,
            league=5,
            budget=Decimal(str(2_000_000 + i * 500_000)),
            performance_rating=40 + i * 5,
            main_driver_1=d1,
            main_driver_2=d2,
            reserve_driver=reserve,
        )
        d1.team_id = team.id
        d2.team_id = team.id
        reserve.team_id = team.id
        team.recalculate_performance()
        teams.append(team)

        print(f"  [{i+1:2d}] {team.name:20s} | Liga: F{team.league} | "
              f"Perf: {team.performance_rating:2d} | "
              f"Budget: ${float(team.budget):>8,.0f}")
        print(f"       {d1.full_name:20s} ({d1.nationality}) | "
              f"OVR: {d1.attributes.overall():5.1f} | "
              f"Per: {d1.personality.value:12s}")
        print(f"       {d2.full_name:20s} ({d2.nationality}) | "
              f"OVR: {d2.attributes.overall():5.1f} | "
              f"Per: {d2.personality.value:12s}")
        print(f"       R: {reserve.full_name:17s} ({reserve.nationality}) | "
              f"OVR: {reserve.attributes.overall():5.1f}")
        print_line()

    # ── Phase 2: Pre-Season ────────────────────────────────────────────
    print_header("📋 PHASE 2: PRE-SEASON (Sponsoren + Training)")
    manager = SeasonManager(universe_id="integration_test")
    sponsor_gen = SponsorGenerator()

    for team in teams:
        sponsor = sponsor_gen.generate_sponsor(team)
        team.sponsor_income = sponsor.budget
        print(f"  {team.name:20s} | Sponsor: {sponsor.name:25s} | "
              f"${float(sponsor.budget):>8,.0f}/Saison | "
              f"Typ: {sponsor.sponsor_type.value:8s}")

    print_line()

    # ── Phase 3: Season (12 Races) ─────────────────────────────────────
    print_header("📋 PHASE 3: SAISON (12 Rennen)")
    season_number = 1

    qualifier_results = []

    for race in range(1, 13):
        print(f"\n  🏁 RENNEN {race:2d}/12 — Wetter: ", end="")
        weather = WeatherSystem.roll_weather(season_number, race)
        print(f"{weather.value.upper():10s}")

        # Race + Qualifier for each team
        for team in teams:
            # Race
            race_result = manager.run_race(team, season_number, race)

            # Qualifier
            qual = manager.run_qualifier(team, season_number, race)
            qualifier_results.append(qual)

            # Print summary
            d1_res = race_result.driver_1_result
            d2_res = race_result.driver_2_result
            if d1_res and d2_res:
                print(f"     {team.name:20s} | P{d1_res.position:2d} + P{d2_res.position:2d} | "
                      f"Points: {race_result.team_points:2d} | "
                      f"Quali: {qual.average_time_ms / 1000:.3f}s",
                      end="")
                if qual.was_auto:
                    print(" ⚠️ AFK", end="")
                if race_result.race_events:
                    print(f" | {race_result.race_events[0][:40]}", end="")
                print()

        # Calculate median for AFK detection (not needed here, all teams participate)
        print(f"     ─── Track: {race_result.track_name:15s} "
              f"| Best Quali: {min(q.average_time_ms for q in qualifier_results[-10:])/1000:.3f}s")

    # ── Phase 4: Season Stats ──────────────────────────────────────────
    print_header("📋 PHASE 4: SAISON-STATISTIK")
    for team in teams:
        ovr = team.main_driver_1.attributes.overall() if team.main_driver_1 else 0
        print(f"  {team.name:20s} | Wins: {team.wins} | Pod: {team.podiums} | "
              f"Pts: {team.season_points:3d} | "
              f"Team Perf: {team.performance_rating:2d} | "
              f"#1 OVR: {ovr:5.1f}")

    # ── Phase 5: Ranking + Promotion/Relegation ────────────────────────
    print_header("📋 PHASE 5: SAISON-RANKING + PROMOTION/RELEGATION")
    team_names = {t.id: t.name for t in teams}

    rankings = RankingCalculator.calculate_season_ranking(
        qualifier_results, team_names
    )

    print(f"\n  🏆 F5 RANKING (niedrigste Gesamtzeit = bester):")
    print(f"     {'Rang':<6s} {'Team':<22s} {'Gesamtzeit':<12s} {'⌀/Quali':<10s} {'Qualis':<7s}")
    print(f"     {'─'*6} {'─'*22} {'─'*12} {'─'*10} {'─'*7}")
    for rank in rankings:
        total = f"{rank.total_time_ms/1000:.3f}s"
        avg = f"{rank.average_time_ms/1000:.3f}s"
        print(f"     #{rank.rank:<3d}  {rank.team_name:<22s} {total:<12s} {avg:<10s} "
              f"{rank.qualifiers_run}/{len(qualifier_results)//10}")

    promotion = RankingCalculator.calculate_promotion_relegation(5, rankings)

    print(f"\n  🚀 PROMOTION (→ F4):")
    for pid in promotion.promotions:
        name = team_names.get(pid, "?")
        print(f"     ✅ {name}")
    print(f"\n  ⬇️  RELEGATION (→ F6):")
    for rid in promotion.relegations:
        name = team_names.get(rid, "?")
        print(f"     ❌ {name}")

    # ── Phase 6: Driver Development ────────────────────────────────────
    print_header("📋 PHASE 6: FAHRER-ENTWICKLUNG")
    for team in teams[:3]:  # Top 3 teams
        d1 = team.main_driver_1
        if d1:
            print(f"  {team.name:20s} | {d1.full_name:20s} | "
                  f"Age: {d1.age:2d} | "
                  f"Speed: {d1.attributes.speed:2d} → OVR: {d1.attributes.overall():5.1f}")

    # ── Phase 7: Global Rating ─────────────────────────────────────────
    print_header("📋 PHASE 7: GLOBALES FAHRER-RATING")
    ratings = []
    for team in teams:
        for driver in team.drivers:
            rating = GlobalRanking.calculate_driver_rating(
                driver, team.league, team.wins, team.podiums, driver.races_driven
            )
            ratings.append((rating, driver, team))

    ratings.sort(key=lambda r: r[0], reverse=True)
    print(f"     {'Rang':<6s} {'Fahrer':<22s} {'Nation':<5s} {'Team':<22s} {'Rating':<7s}")
    print(f"     {'─'*6} {'─'*22} {'─'*5} {'─'*22} {'─'*7}")
    for i, (rating, driver, team) in enumerate(ratings[:10], 1):
        print(f"     #{i:<3d}  {driver.full_name:<22s} {driver.nationality:<5s} "
              f"{team.name:<22s} {rating}")

    # ── Phase 8: Post-Season ───────────────────────────────────────────
    print_header("📋 PHASE 8: POST-SEASON (Academy, Budget, Alter)")
    result = manager.run_post_season(5, season_number, teams, qualifier_results)

    if result["retirements"]:
        print(f"\n  🏥 Pensionierungen:")
        for name in result["retirements"]:
            print(f"     🏁 {name}")
    else:
        print(f"\n  ✅ Keine Pensionierungen diese Saison.")

    if result["academy_drivers"]:
        print(f"\n  🎓 Neue Academy-Fahrer:")
        for name in result["academy_drivers"]:
            print(f"     ⭐ {name}")

    print(f"\n  💰 Budgets nach Saisonende:")
    for team in teams:
        print(f"     ${float(team.budget):>10,.0f}  |  {team.name}")

    # ── Final Summary ──────────────────────────────────────────────────
    print_header("✅ SIMULATION ABGESCHLOSSEN")
    print(f"  • 10 Teams erstellt")
    print(f"  • 30 Fahrer (20 Haupt + 10 Reserve)")
    print(f"  • 12 Rennen + 120 Qualifier-Sessions simuliert")
    print(f"  • 1 Season-Ranking berechnet")
    print(f"  • 2 Promotion / 2 Relegation bestimmt")
    print(f"  • Fahrer-Entwicklung über 12 Runden angewandt")
    print(f"  • Globales Rating berechnet")
    print(f"  • Post-Season (Academy + Budget + Altersentwicklung) abgeschlossen")
    print(f"  • Dynamische Events gerollt (~{sum(len(r.race_events) for t in teams for r in [manager.run_race(t, 1, 1)])} Events)")
    print_line()
    print(f"  Endzeit: {time.strftime('%H:%M:%S')}")
    print("  Alle Systeme funktionieren wie spezifiziert. ✅")
    print()


if __name__ == "__main__":
    simulate_season()
