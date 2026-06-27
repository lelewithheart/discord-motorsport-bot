"""Race commands cog."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.simulation.engine import SimulationEngine, WeatherSystem
from motorsport.systems.events import EventEngine
from motorsport.simulation.driver_generator import DriverDevelopment
from motorsport.data.repository import TeamRepo, DriverRepo
from motorsport.data.database import get_session_maker
from motorsport.data.models import RaceResultModel
from bot.embeds import race_embed
from datetime import datetime


class RaceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()
        self.engine = SimulationEngine(universe_id="discord")
        self.driver_dev = DriverDevelopment()
        self.events = EventEngine()

    @app_commands.command(name="race", description="Simuliere das nächste Rennen")
    async def race(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Du hast kein Team. Erstelle eines mit `/team_create`")
                return

            db_team = teams[0]
            team = await self._load_team(session, db_team)

            if not team.main_driver_1 or not team.main_driver_2:
                await interaction.followup.send("❌ Du brauchst 2 Hauptfahrer für ein Rennen!")
                return

            race_number = team.current_race + 1
            season = team.active_season

            # Run race
            result = self.engine.simulate_race(team, season, race_number)

            # Driver development
            for i, driver in enumerate([team.main_driver_1, team.main_driver_2]):
                driver_result = result.driver_1_result if i == 0 else result.driver_2_result
                if driver_result and not driver_result.dnfs:
                    score = max(0, 1.0 - (driver_result.position - 1) * 0.1)
                    self.driver_dev.develop(driver, team.performance_rating, score)
                    driver.races_driven += 1

            # Events
            for driver in [team.main_driver_1, team.main_driver_2]:
                events = self.events.roll_events(driver, team, season, race_number)
                for event in events:
                    self.events.apply_event(driver, team, event)
                    result.race_events.append(event.description)

            # Update team
            team.current_race = race_number
            team.season_points += result.team_points
            driver_results = [result.driver_1_result, result.driver_2_result]
            for dr in driver_results:
                if dr and dr.position == 1:
                    team.wins += 1
                if dr and dr.position <= 3:
                    team.podiums += 1

            team.recalculate_performance()

            # Save race result
            race_model = RaceResultModel(
                team_id=db_team.id,
                season=season,
                race_number=race_number,
                track_name=result.track_name,
                weather=result.weather.value,
                driver_1_position=result.driver_1_result.position if result.driver_1_result else None,
                driver_2_position=result.driver_2_result.position if result.driver_2_result else None,
                driver_1_time_ms=result.driver_1_result.total_time_ms if result.driver_1_result else None,
                driver_2_time_ms=result.driver_2_result.total_time_ms if result.driver_2_result else None,
                team_points=result.team_points,
                race_events=result.race_events,
                simulated_at=datetime.utcnow(),
            )
            session.add(race_model)

            # Update DB team stats
            db_team.current_race = race_number
            db_team.season_points = team.season_points
            db_team.wins = team.wins
            db_team.podiums = team.podiums
            db_team.performance_rating = team.performance_rating
            await session.commit()

        embed = race_embed(result, team)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="race_result", description="Letztes Rennergebnis")
    async def race_result(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.response.send_message("❌ Kein Team gefunden")
                return

            db_team = teams[0]
            team = await self._load_team(session, db_team)

        embed = discord.Embed(
            title=f"Letztes Rennen: Runde {team.current_race}",
            colour=0x3498DB,
            description=f"Saison {team.active_season} • {team.wins} Siege • {team.season_points} Punkte",
        )
        embed.add_field(name="Team Perf", value=f"{team.performance_rating}/100")
        await interaction.response.send_message(embed=embed)

    async def _load_team(self, session, db_team):
        from motorsport.models import Team, Driver, DriverAttributes, HiddenStats, Personality, DriverSlot
        db_drivers = await DriverRepo.get_by_team(session, db_team.id)

        team = Team(
            id=db_team.id, name=db_team.name, owner_id=db_team.owner_id,
            league=db_team.league, budget=db_team.budget,
            performance_rating=db_team.performance_rating,
            infrastructure_level=db_team.infrastructure_level,
            wins=db_team.wins, podiums=db_team.podiums,
            season_points=db_team.season_points,
            total_qualifier_time_ms=db_team.total_qualifier_time_ms,
            qualifier_count=db_team.qualifier_count,
            active_season=db_team.active_season,
            current_race=db_team.current_race,
        )

        for db_d in db_drivers:
            d = Driver(
                id=db_d.id, first_name=db_d.first_name, last_name=db_d.last_name,
                nationality=db_d.nationality, age=db_d.age,
                attributes=DriverAttributes(
                    speed=db_d.speed, consistency=db_d.consistency,
                    racecraft=db_d.racecraft, overtaking=db_d.overtaking,
                    tyre_management=db_d.tyre_management,
                    qualifying_pace=db_d.qualifying_pace,
                    wet_performance=db_d.wet_performance,
                    mental_strength=db_d.mental_strength,
                ),
                hidden=HiddenStats(
                    potential=db_d.potential, growth_rate=db_d.growth_rate,
                    aggression=db_d.aggression, risk_taking=db_d.risk_taking,
                    pressure_handling=db_d.pressure_handling,
                ),
                personality=Personality(db_d.personality),
                morale=db_d.morale, wins=db_d.wins, podiums=db_d.podiums,
                races_driven=db_d.races_driven,
            )
            if db_d.slot == 1:
                team.main_driver_1 = d
            elif db_d.slot == 2:
                team.main_driver_2 = d
            elif db_d.slot == 3:
                team.reserve_driver = d

        return team
