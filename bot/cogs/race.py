"""Race commands cog — V2: shows schedule + past results."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from datetime import date, datetime
from motorsport.data.database import get_session_maker
from motorsport.data.repository import TeamRepo, RaceScheduleRepo, TrackRepo
from motorsport.data.models import RaceResultModel
from bot.embeds import E, C
from sqlalchemy import select


class RaceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="race", description="Nächstes Rennen & Schedule")
    async def race_next(self, interaction: discord.Interaction):
        """Show upcoming races."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            team = teams[0]

            schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )

            if not schedule:
                await interaction.followup.send(
                    "📅 Noch kein Rennkalender erstellt. "
                    "Rennen starten automatisch um 20:00 sobald die Saison beginnt."
                )
                return

            embed = discord.Embed(
                title=f"🏁 Rennkalender — Saison {team.active_season}",
                colour=0xE10600,
            )

            upcoming = [s for s in schedule if not s.is_completed]
            completed = [s for s in schedule if s.is_completed]

            if upcoming:
                next_race = upcoming[0]
                track = await TrackRepo.get_by_id(session, next_race.track_id)
                track_name = track.name if track else "?"
                days_until = (next_race.race_date - date.today()).days
                countdown = "HEUTE! ⏰" if days_until == 0 else f"in {days_until} Tag(en)"

                embed.description = (
                    f"**Nächstes Rennen:** R{next_race.race_number} — {track_name}\n"
                    f"**Datum:** {next_race.race_date} ({countdown})\n"
                    f"**Quali-Deadline:** 19:30\n"
                    f"**Rennen:** Automatisch um 20:00"
                )

                # Show all upcoming
                lines = []
                for s in upcoming[:5]:
                    t = await TrackRepo.get_by_id(session, s.track_id)
                    tn = t.name if t else "?"
                    lines.append(f"R{s.race_number}: {tn} ({s.race_date})")
                if lines:
                    embed.add_field(name="📅 Kommende Rennen", value="\n".join(lines), inline=False)
            else:
                embed.description = "✅ Alle Rennen dieser Saison abgeschlossen!"

            if completed:
                embed.set_footer(text=f"✅ {len(completed)}/{len(schedule)} Rennen gefahren")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="race_result", description="Letztes Rennergebnis")
    async def race_result(self, interaction: discord.Interaction):
        """Show last race result from DB."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            team = teams[0]

            # Get latest race result from DB
            result = await session.execute(
                select(RaceResultModel)
                .where(RaceResultModel.team_id == team.id)
                .order_by(RaceResultModel.race_number.desc())
                .limit(1)
            )
            race_result = result.scalar_one_or_none()

            if not race_result:
                await interaction.followup.send(
                    "🏁 Noch kein Rennen gefahren. Das erste Rennen startet automatisch um 20:00!"
                )
                return

            # Build embed
            embed = discord.Embed(
                title=f"🏁 Rennen {race_result.race_number} — {race_result.track_name}",
                colour=0xE10600,
                description=f"Weather: {race_result.weather} • Saison {race_result.season}",
            )

            d1_pos = race_result.driver_1_position
            d2_pos = race_result.driver_2_position
            if d1_pos is not None:
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(d1_pos, f"P{d1_pos}")
                time_s = (race_result.driver_1_time_ms or 0) / 1000
                dnf = "💥 DNF" if time_s > 99999 else f"{time_s:.3f}s"
                embed.add_field(name=f"Fahrer 1", value=f"{medal} • {dnf}", inline=True)
            if d2_pos is not None:
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(d2_pos, f"P{d2_pos}")
                time_s = (race_result.driver_2_time_ms or 0) / 1000
                dnf = "💥 DNF" if time_s > 99999 else f"{time_s:.3f}s"
                embed.add_field(name=f"Fahrer 2", value=f"{medal} • {dnf}", inline=True)

            embed.add_field(name="Punkte", value=str(race_result.team_points), inline=True)

            if race_result.race_events:
                embed.add_field(name="Ereignisse", value="\n".join(race_result.race_events[:3]), inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RaceCog(bot))
