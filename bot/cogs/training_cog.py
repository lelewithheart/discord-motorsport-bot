"""Training commands cog — run practice laps and earn R&D points."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.data.database import get_session_maker
from motorsport.data.repository import (
    TeamRepo,
    DriverRepo,
    SetupRepo,
    TrackRepo,
    TrainingRepo,
    RndRepo,
    RaceScheduleRepo,
)
from motorsport.systems.training import TrainingEngine


class TrainingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    # ── helpers ──────────────────────────────────────────────────────────

    async def _get_user_team(self, session, user_id: int):
        teams = await TeamRepo.get_by_owner(session, user_id)
        return teams[0] if teams else None

    async def _get_current_track(self, session, team) -> TrackModel | None:
        schedule = await RaceScheduleRepo.get_by_season(
            session, team.active_season
        )
        if not schedule:
            # Auto-generate schedule
            await TrackRepo.seed_if_empty(session)
            all_tracks = await TrackRepo.get_all(session)
            if all_tracks:
                await RaceScheduleRepo.generate_schedule(
                    session, team.active_season, all_tracks
                )
            schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )
        for s in schedule:
            if not s.is_completed:
                from motorsport.data.repository import TrackRepo
                return await TrackRepo.get_by_id(session, s.track_id)
        return None

    async def _get_current_race_number(self, session, team) -> int:
        schedule = await RaceScheduleRepo.get_by_season(
            session, team.active_season
        )
        if not schedule:
            # Auto-generate schedule
            await TrackRepo.seed_if_empty(session)
            all_tracks = await TrackRepo.get_all(session)
            if all_tracks:
                await RaceScheduleRepo.generate_schedule(
                    session, team.active_season, all_tracks
                )
            schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )
        for s in schedule:
            if not s.is_completed:
                return s.race_number
        return team.current_race + 1

    async def _get_active_setup(self, session, team, track: TrackModel | None):
        """Return a usable setup (track-specific, default, or fresh)."""
        if track:
            track_setups = await SetupRepo.get_by_track(session, team.id, track.id)
            if track_setups:
                return track_setups[0]
        default = await SetupRepo.get_default(session, team.id)
        if default:
            return default
        return await SetupRepo.create(session, team.id, "Default", track_id=None)

    async def _driver_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                return []
            drivers = await DriverRepo.get_by_team(session, team.id)
        choices = []
        for d in drivers:
            label = f"{d.first_name} {d.last_name} ({d.id[:8]}...)"
            if current.lower() in d.id[:8].lower() or current.lower() in d.first_name.lower():
                choices.append(app_commands.Choice(name=label, value=d.id))
        return choices[:25]

    # ── /train command ──────────────────────────────────────────────────

    @app_commands.command(name="train", description="Run training laps for a driver")
    @app_commands.describe(
        driver_id="Driver ID",
        laps="Number of laps (1-20, max 20 total per team per day)",
    )
    @app_commands.autocomplete(driver_id=_driver_autocomplete)
    async def train(
        self, interaction: discord.Interaction, driver_id: str, laps: int
    ):
        laps = max(1, min(20, laps))
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team. Erstelle eines mit `/team_create`")
                return

            # ── Check driver hasn't already trained today ──────────
            existing_driver = [t for t in existing if t.driver_id == driver_id]
            if existing_driver:
                await interaction.followup.send(
                    f"❌ **{db_driver.first_name} {db_driver.last_name}** wurde heute bereits trainiert! "
                    f"(Runde{'n' if existing_driver[0].lap_count != 1 else ''}: "
                    f"{existing_driver[0].lap_count})\n"
                    f"Jeder Fahrer kann nur **1x pro Tag** trainieren."
                )
                return

            # ── Check daily lap limit ────────────────────────────────
            race_number = await self._get_current_race_number(session, team)
            existing = await TrainingRepo.get_by_team_race(
                session, team.id, team.active_season, race_number
            )
            total_laps_done = sum(t.lap_count for t in existing)
            remaining = TrainingEngine.MAX_TRAINING_LAPS_PER_DAY - total_laps_done

            if laps > remaining:
                await interaction.followup.send(
                    f"⚠️ Nur noch **{remaining}** Trainingsrunde{'n' if remaining != 1 else ''} "
                    f"übrig heute (max {TrainingEngine.MAX_TRAINING_LAPS_PER_DAY} pro Team/Tag)!"
                )
                return

            # ── Get driver ───────────────────────────────────────────
            db_driver = await DriverRepo.get(session, driver_id)
            if not db_driver or db_driver.team_id != team.id:
                await interaction.followup.send("❌ Fahrer nicht in deinem Team!")
                return

            # ── Get track & setup ────────────────────────────────────
            track = await self._get_current_track(session, team)
            setup = await self._get_active_setup(session, team, track)

            # ── Build driver attrs dict ──────────────────────────────
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

            # ── Run training simulation ──────────────────────────────
            result = TrainingEngine.run_training(
                driver_attrs,
                setup,
                track,
                laps,
                personality=db_driver.personality,
            )

            # ── Save training session ────────────────────────────────
            ts = await TrainingRepo.get_or_create(
                session,
                team.id,
                driver_id,
                track.id if track else "unknown",
                team.active_season,
                race_number,
            )
            ts.lap_count += laps
            if result["best_lap"] < (ts.best_lap_ms or 999_999_999):
                ts.best_lap_ms = result["best_lap"]
            # Update avg as weighted average
            if ts.avg_lap_ms is not None:
                total_old = ts.avg_lap_ms * (ts.lap_count - laps)
                ts.avg_lap_ms = (total_old + result["avg_lap"] * laps) // ts.lap_count
            else:
                ts.avg_lap_ms = result["avg_lap"]
            ts.setup_id = setup.id
            await TrainingRepo.update(session, ts)

            # ── Award R&D points ─────────────────────────────────────
            rnd_earned = result["rnd_points_earned"]
            total_rnd = await RndRepo.add_points(
                session, team.id, team.active_season, rnd_earned
            )

        # ── Build result embed ────────────────────────────────────────
        track_name = track.name if track else "?"
        best_str = f"{result['best_lap'] / 1000:.3f}s"
        avg_str = f"{result['avg_lap'] / 1000:.3f}s"

        embed = discord.Embed(
            title=f"🏎️ Training — {db_driver.first_name} {db_driver.last_name}",
            colour=0x00FF00,
            description=(
                f"**Track:** {track_name}\n"
                f"**Runden:** {laps} | **Best:** {best_str} 🏆 | **⌀:** {avg_str}\n"
                f"**R&D Punkte:** +{rnd_earned} (Gesamt: {total_rnd})"
            ),
        )

        # Show individual lap times (first 15)
        lap_lines = []
        for i, lap_time in enumerate(result["lap_times"][:15], 1):
            fmt = f"{lap_time / 1000:.3f}s"
            if lap_time == result["best_lap"]:
                fmt += " 🏆"
            lap_lines.append(f"Runde {i}: {fmt}")
        if len(result["lap_times"]) > 15:
            lap_lines.append(f"... +{len(result['lap_times']) - 15} weitere")
        embed.add_field(name="Rundenzeiten", value="\n".join(lap_lines), inline=False)

        await interaction.followup.send(embed=embed)

    # ── /training group ────────────────────────────────────────────────

    training = app_commands.Group(name="training", description="Training status and history")

    @training.command(name="status", description="Show remaining training laps and session log")
    async def training_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            race_number = await self._get_current_race_number(session, team)
            sessions = await TrainingRepo.get_by_team_race(
                session, team.id, team.active_season, race_number
            )
            total_laps_done = sum(t.lap_count for t in sessions)
            remaining = TrainingEngine.MAX_TRAINING_LAPS_PER_DAY - total_laps_done

            drivers = await DriverRepo.get_by_team(session, team.id)
            driver_map = {d.id: d for d in drivers}

        embed = discord.Embed(
            title=f"📊 Training Status — Rennen {race_number}",
            colour=0x3498DB,
            description=(
                f"**Verbrauchte Runden:** {total_laps_done} "
                f"/ {TrainingEngine.MAX_TRAINING_LAPS_PER_DAY}\n"
                f"**Verbleibend:** {remaining} Runde{'n' if remaining != 1 else ''}"
            ),
        )

        if not sessions:
            embed.add_field(
                name="Heutige Sessions",
                value="Noch kein Training absolviert.",
                inline=False,
            )
        else:
            for ts in sessions:
                driver = driver_map.get(ts.driver_id)
                driver_name = (
                    f"{driver.first_name} {driver.last_name}" if driver else ts.driver_id[:8]
                )
                best = (
                    f"{ts.best_lap_ms / 1000:.3f}s"
                    if ts.best_lap_ms
                    else "—"
                )
                avg = (
                    f"{ts.avg_lap_ms / 1000:.3f}s"
                    if ts.avg_lap_ms
                    else "—"
                )
                embed.add_field(
                    name=f"🏁 {driver_name}",
                    value=f"Runden: {ts.lap_count} | Best: {best} | ⌀: {avg}",
                    inline=False,
                )

        if remaining > 0:
            embed.set_footer(text=f"💡 Noch {remaining} Runden verfügbar — /train <driver> <laps>")
        else:
            embed.set_footer(text="⏰ Tägliches Trainingslimit erreicht!")

        await interaction.followup.send(embed=embed)

    @training.command(name="history", description="Show training history for this season")
    async def training_history(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )
            drivers = await DriverRepo.get_by_team(session, team.id)
            driver_map = {d.id: d for d in drivers}

            # Collect all training sessions for the season
            all_sessions = []
            for rs in schedule:
                ss = await TrainingRepo.get_by_team_race(
                    session, team.id, team.active_season, rs.race_number
                )
                all_sessions.extend(ss)

        if not all_sessions:
            embed = discord.Embed(
                title="📜 Trainings-Historie",
                colour=0x3498DB,
                description="Diese Saison wurden noch keine Trainingsrunden gefahren.",
            )
            await interaction.followup.send(embed=embed)
            return

        # Organize by race number
        by_race: dict[int, list] = {}
        for ts in all_sessions:
            by_race.setdefault(ts.race_number, []).append(ts)

        embed = discord.Embed(
            title=f"📜 Trainings-Historie — Saison {team.active_season}",
            colour=0x3498DB,
            description=f"**Team:** {team.name} | {len(all_sessions)} Sessions",
        )

        total_laps = 0
        total_best = float("inf")
        total_rnd = 0

        for race_num in sorted(by_race.keys()):
            sessions = by_race[race_num]
            lines = []
            for ts in sessions:
                driver = driver_map.get(ts.driver_id)
                driver_name = (
                    f"{driver.first_name} {driver.last_name}" if driver else ts.driver_id[:8]
                )
                best = (
                    f"{ts.best_lap_ms / 1000:.3f}s"
                    if ts.best_lap_ms
                    else "—"
                )
                avg = (
                    f"{ts.avg_lap_ms / 1000:.3f}s"
                    if ts.avg_lap_ms
                    else "—"
                )
                lines.append(
                    f"**{driver_name}**: {ts.lap_count} Runden | Best {best} | ⌀ {avg}"
                )
                total_laps += ts.lap_count
                if ts.best_lap_ms and ts.best_lap_ms < total_best:
                    total_best = ts.best_lap_ms
                total_rnd += ts.lap_count * TrainingEngine.RND_POINTS_PER_LAP

            embed.add_field(
                name=f"🏁 Rennen {race_num}",
                value="\n".join(lines) if lines else "—",
                inline=False,
            )

        total_best_str = (
            f"{total_best / 1000:.3f}s" if total_best != float("inf") else "—"
        )
        embed.set_footer(
            text=f"📊 Gesamt: {total_laps} Runden | Best: {total_best_str} | R&D: +{total_rnd}"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(TrainingCog(bot))
