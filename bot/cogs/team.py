"""Team commands cog."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.models import Team, Driver, DriverSlot
from motorsport.simulation.driver_generator import DriverGenerator
from motorsport.data.repository import TeamRepo, DriverRepo, PlayerRepo
from motorsport.data.database import get_session_maker
from bot.embeds import team_embed


class TeamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="team", description="Deine Team-Übersicht")
    async def team_overview(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
        if not teams:
            embed = discord.Embed(
                title="Kein Team",
                description="Du hast noch kein Team. Erstelle eines mit `/team create`",
                colour=0xFFAA00,
            )
            await interaction.response.send_message(embed=embed)
            return

        # Convert DB model to dataclass for embed
        db_team = teams[0]
        team = self._db_to_team(db_team, session)
        embed = team_embed(team)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="team_create", description="Erstelle ein neues Team")
    @app_commands.describe(name="Team-Name")
    async def team_create(self, interaction: discord.Interaction, name: str):
        async with self.session_maker() as session:
            player = await PlayerRepo.get_or_create(session, interaction.user.id,
                                                     interaction.user.name)
            existing = await TeamRepo.get_by_owner(session, interaction.user.id)
            if len(existing) >= (3 if player.is_premium else 1):
                embed = discord.Embed(
                    title="❌ Limit erreicht",
                    description=f"Maximal {'3' if player.is_premium else '1'} Teams erlaubt. "
                                f"{'⭐ Premium' if not player.is_premium else ''}",
                    colour=0xFF0000,
                )
                await interaction.response.send_message(embed=embed)
                return

            team = await TeamRepo.create(session, interaction.user.id, name)

            # Generate 3 initial drivers
            gen = DriverGenerator()
            for slot, is_academy in [(1, False), (2, False), (3, True)]:
                d = gen.generate_driver(
                    age=18 + slot * 2,
                    is_academy=is_academy,
                )
                await DriverRepo.create(session, {
                    "id": d.id,
                    "team_id": team.id,
                    "first_name": d.first_name,
                    "last_name": d.last_name,
                    "nationality": d.nationality,
                    "age": d.age,
                    "speed": d.attributes.speed,
                    "consistency": d.attributes.consistency,
                    "racecraft": d.attributes.racecraft,
                    "overtaking": d.attributes.overtaking,
                    "tyre_management": d.attributes.tyre_management,
                    "qualifying_pace": d.attributes.qualifying_pace,
                    "wet_performance": d.attributes.wet_performance,
                    "mental_strength": d.attributes.mental_strength,
                    "potential": d.hidden.potential,
                    "growth_rate": d.hidden.growth_rate,
                    "aggression": d.hidden.aggression,
                    "risk_taking": d.hidden.risk_taking,
                    "pressure_handling": d.hidden.pressure_handling,
                    "personality": d.personality.value,
                    "slot": slot,
                    "is_academy": is_academy,
                    "morale": d.morale,
                })

        embed = discord.Embed(
            title="✅ Team erstellt!",
            description=f"**{name}** ist bereit für die F10-Liga!",
            colour=0x00FF00,
        )
        embed.add_field(name="Fahrer", value="3 Fahrer generiert (2 Haupt + 1 Reserve)")
        embed.add_field(name="Budget", value="$1,000,000")
        embed.add_field(name="Nächster Schritt", value="`/team` für Übersicht")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="team_lineup", description="Aufstellung ändern")
    @app_commands.describe(driver_1="Fahrer-ID für Slot 1",
                           driver_2="Fahrer-ID für Slot 2",
                           reserve="Fahrer-ID für Reserve")
    async def team_lineup(self, interaction: discord.Interaction,
                          driver_1: str = None, driver_2: str = None,
                          reserve: str = None):
        await interaction.response.send_message(
            "⚙️ Aufstellungs-Änderung ist im Aufbau. "
            "Nutze `/drivers` um Fahrer-IDs zu sehen.",
            ephemeral=True
        )

    @app_commands.command(name="team_upgrade", description="Team-Upgrade kaufen")
    @app_commands.describe(upgrade="Upgrade-Typ (aerodynamics, engine, simulator)")
    async def team_upgrade(self, interaction: discord.Interaction,
                           upgrade: str):
        await interaction.response.send_message(
            f"⚙️ Upgrade '{upgrade}' wird implementiert...",
            ephemeral=True
        )

    def _db_to_team(self, db_team, session):
        """Convert DB model to dataclass Team for embed rendering."""
        import asyncio
        drivers_future = DriverRepo.get_by_team(session, db_team.id)
        db_drivers = asyncio.run_coroutine_threadsafe(drivers_future, self.bot.loop).result()

        team = Team(
            id=db_team.id,
            name=db_team.name,
            owner_id=db_team.owner_id,
            league=db_team.league,
            budget=db_team.budget,
            performance_rating=db_team.performance_rating,
            infrastructure_level=db_team.infrastructure_level,
            wins=db_team.wins,
            podiums=db_team.podiums,
            season_points=db_team.season_points,
            total_qualifier_time_ms=db_team.total_qualifier_time_ms,
            qualifier_count=db_team.qualifier_count,
            is_premium=db_team.is_premium,
            active_season=db_team.active_season,
            current_race=db_team.current_race,
        )

        for db_d in db_drivers:
            from motorsport.models import DriverAttributes, HiddenStats
            d = Driver(
                id=db_d.id,
                first_name=db_d.first_name,
                last_name=db_d.last_name,
                nationality=db_d.nationality,
                age=db_d.age,
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
                personality=db_d.personality,
                slot=DriverSlot(db_d.slot) if db_d.slot else None,
                morale=db_d.morale,
                wins=db_d.wins, podiums=db_d.podiums,
                races_driven=db_d.races_driven,
                is_academy=db_d.is_academy,
            )
            if db_d.slot == 1:
                team.main_driver_1 = d
            elif db_d.slot == 2:
                team.main_driver_2 = d
            elif db_d.slot == 3:
                team.reserve_driver = d

        return team
