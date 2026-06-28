"""Qualifier commands cog — V2: hotlap qualifier with training engine."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from datetime import date, datetime, time
from motorsport.data.database import get_session_maker
from motorsport.data.repository import (
    TeamRepo, DriverRepo, QualifierRepo, SetupRepo,
    TrackRepo, RaceScheduleRepo, TrainingRepo,
)
from motorsport.data.models import QualifierModel
from motorsport.systems.training import TrainingEngine


class QualifierCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    async def _get_user_team(self, session, user_id: int):
        teams = await TeamRepo.get_by_owner(session, user_id)
        return teams[0] if teams else None

    async def _get_current_race_data(self, session, team):
        """Get (schedule_entry, track) for the next upcoming race."""
        schedule = await RaceScheduleRepo.get_by_season(
            session, team.active_season
        )
        if not schedule:
            return None, None
        for s in schedule:
            if not s.is_completed:
                track = await TrackRepo.get_by_id(session, s.track_id)
                return s, track
        return None, None

    # ── /qualifier — Status overview ────────────────────────────────────

    @app_commands.command(name="qualifier", description="Qualifier-Status & Deadline")
    async def qualifier_status(self, interaction: discord.Interaction):
        """Show current qualifier status with deadline and position."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team. Erstelle eines mit `/team_create`")
                return

            sched_entry, track = await self._get_current_race_data(session, team)
            if not sched_entry:
                await interaction.followup.send("📅 Kein aktuelles Rennwochenende gefunden.")
                return

            track_name = track.name if track else "?"
            deadline = sched_entry.qualifier_deadline
            deadline_str = deadline.strftime("%d.%m.%Y %H:%M") if deadline else "19:30"

            # Check if user already ran qualifier
            existing_q = await QualifierRepo.get_by_team_race(
                session, team.id, team.active_season, sched_entry.race_number
            )

            embed = discord.Embed(
                title=f"⏱️ Qualifier — Rennen {sched_entry.race_number}",
                colour=0x3498DB,
                description=(
                    f"**Track:** {track_name}\n"
                    f"**Deadline:** {deadline_str}\n"
                    f"**Rennen:** Automatisch um 20:00\n"
                ),
            )

            if existing_q:
                avg_ms = existing_q.average_time_ms
                embed.add_field(name="✅ Qualifikation abgeschlossen",
                                value=f"⌀ Teamzeit: **{avg_ms/1000:.3f}s**",
                                inline=False)
            else:
                time_now = datetime.now()
                if deadline and time_now > deadline:
                    embed.add_field(
                        name="⏰ Deadline verstrichen",
                        value="Es wird eine Standardzeit verwendet.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="⌛ Offen",
                        value="Nutze `/qualifier run`, um eine schnelle Runde zu fahren!",
                        inline=False,
                    )

            # Show current average position based on all qualifiers for this race
            all_qs = await QualifierRepo.get_all_by_race(
                session, team.league, team.active_season, sched_entry.race_number
            )
            if all_qs:
                sorted_qs = sorted(all_qs, key=lambda q: q.average_time_ms)
                position = next((i + 1 for i, q in enumerate(sorted_qs) if q.team_id == team.id), None)
                if position:
                    embed.add_field(name="🏁 Aktuelle Position",
                                    value=f"**P{position}** von {len(sorted_qs)} Teams",
                                    inline=True)
                embed.add_field(name="Teams mit Quali",
                                value=str(len(sorted_qs)),
                                inline=True)

            embed.set_footer(text=f"Liga F{team.league} • Saison {team.active_season}")

        await interaction.followup.send(embed=embed)

    # ── /qualifier run — Hotlap ─────────────────────────────────────────

    @app_commands.command(name="qualifier_run", description="Fahre eine Qualifier-Runde")
    async def qualifier_run(self, interaction: discord.Interaction):
        """Run a single hotlap qualifier with current setup + driver stats."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            db_drivers = await DriverRepo.get_by_team(session, team.id)
            main_drivers = [d for d in db_drivers if d.slot in (1, 2)]
            if len(main_drivers) < 2:
                await interaction.followup.send("❌ Du brauchst 2 Hauptfahrer für den Qualifier!")
                return

            sched_entry, track = await self._get_current_race_data(session, team)
            if not sched_entry:
                await interaction.followup.send("📅 Kein aktuelles Rennwochenende.")
                return
            if not track:
                await interaction.followup.send("❌ Keine Streckendaten gefunden.")
                return

            # Check deadline
            deadline = sched_entry.qualifier_deadline
            if deadline and datetime.now() > deadline:
                await interaction.followup.send(
                    "⏰ Die Qualifier-Deadline (19:30) ist bereits verstrichen. "
                    "Es wird eine Standardzeit verwendet."
                )
                return

            # Check if already ran
            existing_q = await QualifierRepo.get_by_team_race(
                session, team.id, team.active_season, sched_entry.race_number
            )
            if existing_q:
                await interaction.followup.send(
                    f"✅ Du hast bereits einen Qualifier für Rennen {sched_entry.race_number} gefahren! "
                    f"⌀ Zeit: {existing_q.average_time_ms/1000:.3f}s"
                )
                return

            # Get setup for this track
            setup = await SetupRepo.get_by_track(session, team.id, track.id)
            if not setup:
                setup = await SetupRepo.get_default(session, team.id)
            if not setup:
                setup = await SetupRepo.create(session, team.id, "Default", track_id=None)

            total_time_ms = 0
            driver_results = []

            for db_driver in main_drivers:
                driver_attrs = {
                    "speed": db_driver.speed,
                    "consistency": db_driver.consistency,
                    "racecraft": db_driver.racecraft,
                    "overtaking": db_driver.overtaking,
                    "tyre_management": db_driver.tyre_management,
                    "qualifying_pace": db_driver.qualifying_pace,
                    "wet_performance": db_driver.wet_performance,
                    "mental_strength": db_driver.mental_strength,
                }

                # Run a single hotlap
                result = TrainingEngine.run_training(
                    driver_attrs,
                    setup,
                    track,
                    laps=1,
                    personality=db_driver.personality,
                )
                lap_ms = result["best_lap"]
                total_time_ms += lap_ms
                driver_results.append({
                    "driver": db_driver,
                    "lap_ms": lap_ms,
                })

            avg_time_ms = total_time_ms // len(main_drivers)

            # Save qualifier result
            qm = QualifierModel(
                team_id=team.id,
                league=team.league,
                season=team.active_season,
                race_number=sched_entry.race_number,
                driver_1_time_ms=driver_results[0]["lap_ms"] if len(driver_results) > 0 else None,
                driver_2_time_ms=driver_results[1]["lap_ms"] if len(driver_results) > 1 else None,
                average_time_ms=avg_time_ms,
                was_auto=False,
            )
            session.add(qm)

            # Update team stats
            team.total_qualifier_time_ms += avg_time_ms
            team.qualifier_count += 1
            team.afk_streak = 0
            await session.commit()

        # Build result embed
        embed = discord.Embed(
            title=f"⏱️ Qualifier — Rennen {sched_entry.race_number}",
            colour=0x3498DB,
            description=f"**Track:** {track.name}\n",
        )

        for i, dr in enumerate(driver_results, 1):
            d = dr["driver"]
            time_str = f"{dr['lap_ms']/1000:.3f}s"
            embed.add_field(
                name=f"Fahrer {i}: {d.first_name} {d.last_name}",
                value=f"⏱️ {time_str}",
                inline=True,
            )

        embed.add_field(name="🏁 ⌀ Teamzeit",
                        value=f"**{avg_time_ms/1000:.3f}s**",
                        inline=False)

        await interaction.followup.send(embed=embed)

    # ── /qualifier ranking ──────────────────────────────────────────────

    @app_commands.command(name="qualifier_ranking", description="Liga-Qualifier-Ranking")
    async def qualifier_ranking(self, interaction: discord.Interaction):
        """Show qualifier ranking for the current race."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Kein Team")
                return

            sched_entry, track = await self._get_current_race_data(session, team)
            if not sched_entry:
                await interaction.followup.send("📅 Kein aktuelles Rennwochenende.")
                return

            all_qs = await QualifierRepo.get_all_by_race(
                session, team.league, team.active_season, sched_entry.race_number
            )

            if not all_qs:
                await interaction.followup.send(
                    "📭 Noch keine Qualifier-Zeiten für dieses Rennen."
                )
                return

            sorted_qs = sorted(all_qs, key=lambda q: q.average_time_ms)
            track_name = track.name if track else "?"

            embed = discord.Embed(
                title=f"⏱️ Qualifier-Ranking — Rennen {sched_entry.race_number}",
                colour=0xFFD700,
                description=f"**Track:** {track_name} • {len(sorted_qs)} Teams",
            )

            # Get team names
            team_names = {}
            for q in sorted_qs:
                t = await TeamRepo.get(session, q.team_id)
                team_names[q.team_id] = t.name if t else "?"

            lines = []
            for i, q in enumerate(sorted_qs[:20], 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                name = team_names.get(q.team_id, "?")
                lines.append(f"{medal} **{name}** — {q.average_time_ms/1000:.3f}s")

            embed.add_field(name="Rangliste", value="\n".join(lines), inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(QualifierCog(bot))
