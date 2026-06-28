"""Driver commands cog."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.simulation.driver_generator import DriverDevelopment
from motorsport.data.repository import TeamRepo, DriverRepo
from motorsport.data.database import get_session_maker
from bot.embeds import driver_embed, market_embed


class DriverCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="drivers", description="Zeigt alle Fahrer deines Teams")
    async def drivers_list(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.response.send_message("❌ Kein Team gefunden", ephemeral=True)
                return
            drivers = await DriverRepo.get_by_team(session, teams[0].id)

        if not drivers:
            await interaction.response.send_message("❌ Keine Fahrer im Team", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🏎️ Fahrer — {teams[0].name}",
            colour=0x3498DB,
            description=f"Saison {teams[0].active_season} • {len(drivers)} Fahrer",
        )
        for d in drivers:
            slot_icon = {1: "🥇", 2: "🥈", 3: "🔄"}.get(d.slot, "❓")
            embed.add_field(
                name=f"{slot_icon} {d.first_name} {d.last_name} ({d.nationality})",
                value=f"Alter: {d.age} • OVR: {(d.speed+d.consistency+d.racecraft+d.overtaking+d.tyre_management+d.qualifying_pace+d.wet_performance+d.mental_strength)/8:.1f} • {d.personality.title()}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="driver", description="Details zu einem Fahrer")
    @app_commands.describe(driver_id="Fahrer-ID")
    async def driver_detail(self, interaction: discord.Interaction, driver_id: str):
        async with self.session_maker() as session:
            db_d = await DriverRepo.get(session, driver_id)
            if not db_d:
                await interaction.response.send_message("❌ Fahrer nicht gefunden", ephemeral=True)
                return
            from motorsport.models import Driver, DriverAttributes, HiddenStats, Personality
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
        await interaction.response.send_message(embed=driver_embed(d, "Dein Team"), ephemeral=True)

    @app_commands.command(name="train", description="Training für deine Fahrer")
    async def train(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.response.send_message("❌ Kein Team", ephemeral=True)
                return
            drivers = await DriverRepo.get_by_team(session, teams[0].id)
            dev = DriverDevelopment()
            trained = []
            for db_d in drivers:
                from motorsport.models import Driver, DriverAttributes, HiddenStats, Personality
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
                    morale=db_d.morale,
                )
                dev.develop(d, teams[0].performance_rating, 0.5, 2)
                trained.append(d.full_name)
                db_d.speed = d.attributes.speed
                db_d.consistency = d.attributes.consistency
                # ... update all attrs
            await session.commit()

        embed = discord.Embed(
            title="🏋️ Training abgeschlossen!",
            colour=0x00FF00,
            description="Deine Fahrer haben trainiert:",
        )
        embed.add_field(name="Trainiert", value="\n".join(trained))
        await interaction.response.send_message(embed=embed, ephemeral=True)
