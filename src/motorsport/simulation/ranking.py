"""
Ranking calculator for season-end rankings and promotion/relegation.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from motorsport.models import QualifierResult, TeamRank, League


@dataclass
class PromotionResult:
    """Result of promotion/relegation calculation."""
    league: int
    promotions: list[str] = field(default_factory=list)      # team_ids moving up
    relegations: list[str] = field(default_factory=list)     # team_ids moving down
    promotion_league: Optional[int] = None     # target league for promotions
    relegation_league: Optional[int] = None    # target league for relegations
    playoffs: list[tuple[str, str]] = field(default_factory=list)  # (team_a, team_b) playoff pairs


class RankingCalculator:
    """Calculates season rankings and promotion/relegation."""

    @staticmethod
    def calculate_season_ranking(
        qualifiers: list[QualifierResult],
        team_names: dict[str, str]
    ) -> list[TeamRank]:
        """Sum all qualifier times per team.
        
        Lower total time = better ranking.
        """
        team_data: dict[str, dict] = {}

        for q in qualifiers:
            if q.team_id not in team_data:
                team_data[q.team_id] = {
                    "times": [],
                    "league": q.league,
                }
            team_data[q.team_id]["times"].append(q.average_time_ms)

        rankings = []
        for team_id, data in team_data.items():
            times = data["times"]
            total = sum(times)
            avg = total // len(times)
            rankings.append(TeamRank(
                team_id=team_id,
                team_name=team_names.get(team_id, "Unknown Team"),
                total_time_ms=total,
                average_time_ms=avg,
                qualifiers_run=len(times),
                league=data["league"],
            ))

        # Sort by total time (lowest = best)
        rankings.sort(key=lambda r: r.total_time_ms)

        # Assign ranks
        for i, r in enumerate(rankings, 1):
            r.rank = i

        return rankings

    @staticmethod
    def calculate_promotion_relegation(
        league: int,
        rankings: list[TeamRank],
    ) -> PromotionResult:
        """Determine which teams get promoted and relegated.
        
        Top 2 → Promotion (to league-1)
        Bottom 2 → Relegation (to league+1)
        """
        result = PromotionResult(league=league)

        if len(rankings) < 4:
            return result  # Not enough teams

        # Top 2 promote
        promotions = rankings[:2]
        result.promotions = [r.team_id for r in promotions]
        result.promotion_league = league - 1 if league > 1 else None

        # Bottom 2 relegate
        relegations = rankings[-2:]
        result.relegations = [r.team_id for r in relegations]
        result.relegation_league = league + 1 if league < 10 else None

        return result

    @staticmethod
    def calculate_playoffs(
        rankings: list[TeamRank],
        league: int,
    ) -> PromotionResult:
        """Alternative with playoffs between border positions.
        
        2nd vs 3rd from bottom for relegation playoff.
        """
        result = PromotionResult(league=league)

        if len(rankings) < 5:
            return result

        # Direct promotion
        promotions = rankings[:2]
        result.promotions = [r.team_id for r in promotions]
        result.promotion_league = league - 1 if league > 1 else None

        # Direct relegation (last place)
        direct_rel = rankings[-1:]
        result.relegations = [r.team_id for r in direct_rel]
        result.relegation_league = league + 1 if league < 10 else None

        # Playoff: 2nd last vs 3rd last
        playoff_teams = (rankings[-2].team_id, rankings[-3].team_id)
        result.playoffs = [playoff_teams]

        return result


class GlobalRanking:
    """Global driver ranking across all leagues."""

    @staticmethod
    def calculate_driver_rating(
        driver, league: int, season_wins: int = 0,
        season_podiums: int = 0, races_driven: int = 0
    ) -> int:
        """Calculate a global driver rating (0-1000)."""
        if races_driven == 0:
            return 0

        league_factor = (11 - league) / 10
        overall = sum(driver.attributes.__dict__.values()) / 8

        win_rate = season_wins / max(1, races_driven)
        podium_rate = season_podiums / max(1, races_driven)

        score = (
            overall * 4.0 +           # Base skill: 0-400
            league_factor * 200 +      # League: 0-200
            win_rate * 200 +           # Wins: 0-200
            podium_rate * 100 +        # Podiums: 0-100
            driver.morale * 1.0        # Morale: 0-100
        )

        # Age factor (peak at 25)
        age_factor = 1.0 - abs(driver.age - 25) * 0.01
        score *= max(0.80, age_factor)

        return int(score)
