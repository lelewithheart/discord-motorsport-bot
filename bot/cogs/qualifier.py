"""Qualifier commands cog."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.simulation.engine import SimulationEngine, WeatherSystem
from motorsport.data.repository import TeamRepo, DriverRepo, QualifierRepo
from motorsport.data.database import get_session_maker
from motorsport.data.models import QualifierModel
from bot.embeds import qualifier_embed


class QualifierCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()
        self.engine = SimulationEngine()

    @app_commands.command(name="qualifier", description="Qualifier-Übersicht")
    async def qualifier_overview(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.response.send_message("❌ Kein Team")
                return
            t = teams[0]
        embed = discord.Embed(
            title=f"⏱️ Qualifier — {t.name}",
            colour=0x3498DB,
            description=f"Liga F{t.league} • Saison {t.active_season} • Rennen {t.current_race}",
        )
        if t.total_qualifier_time_ms > 0:
            avg = t.total_qualifier_time_ms / max(1, t.qualifier_count)
            embed.add_field(name="⌀ Qualifier-Zeit", value=f"{avg/1000:.3f}s")
        embed.add_field(name="Teilnahmen", value=str(t.qualifier_count))
        embed.add_field(name="AFK-Streak", value=str(t.afk_streak))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="qualifier_run", description="Qualifier fahren")
    async def qualifier_run(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            db_team = teams[0]

            # Build team from DB
            from motorsport.models import Team, Driver, DriverAttributes, HiddenStats, Personality, DriverSlot
            db_drivers = await DriverRepo.get_by_team(session, db_team.id)
            team = Team(id=db_team.id, name=db_team.name, owner_id=db_team.owner_id,
                       league=db_team.league, budget=db_team.budget,
                       performance_rating=db_team.performance_rating)
            for db_d in db_drivers:
                d = Driver(id=db_d.id, first_name=db_d.first_name, last_name=db_d.last_name,
                          nationality=db_d.nationality, age=db_d.age,
                          attributes=DriverAttributes(speed=db_d.speed, consistency=db_d.consistency,
                                                     racecraft=db_d.racecraft, overtaking=db_d.overtaking,
                                                     tyre_management=db_d.tyre_management,
                                                     qualifying_pace=db_d.qualifying_pace,
                                                     wet_performance=db_d.wet_performance,
                                                     mental_strength=db_d.mental_strength),
                          hidden=HiddenStats(potential=db_d.potential, growth_rate=db_d.growth_rate,
                                            aggression=db_d.aggression, risk_taking=db_d.risk_taking,
                                            pressure_handling=db_d.pressure_handling),
                          personality=Personality(db_d.personality), slot=DriverSlot(db_d.slot) if db_d.slot else None)
                if db_d.slot == 1: team.main_driver_1 = d
                elif db_d.slot == 2: team.main_driver_2 = d
                elif db_d.slot == 3: team.reserve_driver = d

            # Simulate qualifier
            weather = WeatherSystem.roll_weather(db_team.active_season, db_team.current_race + 1)

            from motorsport.simulation.engine import QualifierSystem
            qs = QualifierSystem(self.engine)
            result = qs.run_qualifier(team, db_team.active_season, db_team.current_race + 1, weather)

            # Save
            qm = QualifierModel(
                team_id=db_team.id, league=db_team.league,
                season=db_team.active_season, race_number=db_team.current_race + 1,
                driver_1_time_ms=result.driver_1_time_ms,
                driver_2_time_ms=result.driver_2_time_ms,
                driver_3_time_ms=result.driver_3_time_ms,
                average_time_ms=result.average_time_ms,
                was_auto=False,
            )
            session.add(qm)
            db_team.total_qualifier_time_ms += result.average_time_ms
            db_team.qualifier_count += 1
            db_team.afk_streak = 0
            await session.commit()

        embed = qualifier_embed(result, team)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="qualifier_ranking", description="Liga-Qualifier-Ranking")
    async def qualifier_ranking(self, interaction: discord.Interaction):
        await interaction.response.send_message("📊 Qualifier-Ranking wird geladen...", ephemeral=True)
