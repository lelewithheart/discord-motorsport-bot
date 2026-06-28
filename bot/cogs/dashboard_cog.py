"""Dashboard cog — one-command overview of everything."""
from __future__ import annotations

from datetime import date

import discord
from discord.ext import commands
from discord import app_commands

from motorsport.data.database import get_session_maker
from motorsport.data.repository import (
    TeamRepo,
    DriverRepo,
    RaceScheduleRepo,
    TrackRepo,
    SetupRepo,
    RndRepo,
    TrainingRepo,
)
from motorsport.systems.rnd import RndManager


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _get_user_team(self, session, user_id: int):
        teams = await TeamRepo.get_by_owner(session, user_id)
        return teams[0] if teams else None

    def _calc_driver_ovr(self, driver) -> float:
        """Calculate overall rating from visible stats."""
        return (
            driver.speed + driver.consistency + driver.racecraft
            + driver.overtaking + driver.tyre_management
            + driver.qualifying_pace + driver.wet_performance
            + driver.mental_strength
        ) / 8

    def _morale_emoji(self, value: int) -> str:
        if value >= 80:
            return "🟢"
        elif value >= 50:
            return "🟡"
        elif value >= 30:
            return "🟠"
        return "🔴"

    # ── /dashboard ───────────────────────────────────────────────────────

    @app_commands.command(name="dashboard", description="Alle Infos auf einen Blick")
    async def dashboard(self, interaction: discord.Interaction):
        """Big overview embed — team, next race, setup, training, R&D, drivers, season."""
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send(
                    "❌ Kein Team. Erstelle eines mit `/team_create`"
                )
                return

            # ── Drivers ─────────────────────────────────────────────────
            drivers = await DriverRepo.get_by_team(session, team.id)

            # ── Next race ───────────────────────────────────────────────
            schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )
            next_race = None
            for s in schedule:
                if not s.is_completed:
                    next_race = s
                    break

            track = None
            if next_race:
                track = await TrackRepo.get_by_id(session, next_race.track_id)

            # ── Setup ───────────────────────────────────────────────────
            setup = None
            if track:
                track_setups = await SetupRepo.get_by_track(
                    session, team.id, track.id
                )
                if track_setups:
                    setup = track_setups[0]

            if not setup:
                setup = await SetupRepo.get_default(session, team.id)

            # ── Training ────────────────────────────────────────────────
            race_num = (
                next_race.race_number
                if next_race
                else team.current_race + 1
            )
            training_sessions = await TrainingRepo.get_by_team_race(
                session, team.id, team.active_season, race_num
            )
            total_laps_used = sum(t.lap_count for t in training_sessions)
            trained_drivers = len(training_sessions)

            # ── R&D ─────────────────────────────────────────────────────
            rnd_points = await RndRepo.get_points(
                session, team.id, team.active_season
            )
            upgrades = await RndRepo.get_upgrades(session, team.id)
            bonuses = RndManager.calculate_stat_bonuses(upgrades)

        # ── Build dashboard embed ───────────────────────────────────────

        embed = discord.Embed(
            title=f"🏁 {team.name}",
            colour=0xE10600,
            description=(
                f"📅 Saison {team.active_season}  ·  "
                f"F{team.league}  ·  "
                f"💰 ${float(team.budget):,.0f}"
            ),
        )

        # 1. Next race
        if next_race and track:
            days_until = (next_race.race_date - date.today()).days
            if days_until < 0:
                countdown = "🔴 Läuft heute"
            elif days_until == 0:
                countdown = "⏰ **Heute!**"
            elif days_until == 1:
                countdown = "📅 Morgen"
            else:
                countdown = f"📅 in {days_until} Tagen"

            embed.add_field(
                name="🏎️ Nächstes Rennen",
                value=(
                    f"**R{next_race.race_number} — {track.name}** "
                    f"({track.country or '—'})\n"
                    f"{countdown}  |  Quali-Deadline: 19:30"
                ),
                inline=False,
            )
        else:
            embed.add_field(
                name="🏎️ Nächstes Rennen",
                value="*Kein anstehendes Rennen*",
                inline=False,
            )

        # 2. Setup
        if setup:
            setup_str = (
                f"FW:{setup.front_wing}  RW:{setup.rear_wing}  "
                f"S:{setup.suspension}  G:{setup.gear_ratio}  "
                f"R:{setup.tire_compound}"
            )
            if bonuses:
                bonus_str = " | ".join(
                    f"{stat.title()}+{int(bonus)}"
                    for stat, bonus in sorted(bonuses.items())
                )
                setup_str += f"\n🔬 {bonus_str}"
        else:
            setup_str = "*Kein Setup vorhanden*"

        embed.add_field(name="🔧 Setup", value=setup_str, inline=True)

        # 3. Training
        embed.add_field(
            name="🏋️ Training",
            value=(
                f"{total_laps_used}/20 Runden heute\n"
                f"{trained_drivers} Fahrer trainiert"
            ),
            inline=True,
        )

        # 4. R&D
        embed.add_field(
            name="🔬 R&D",
            value=(
                f"💠 {rnd_points.points} Punkte\n"
                f"{len(upgrades)} Komponente(n) upgradiert"
            ),
            inline=True,
        )

        # 5. Drivers
        if drivers:
            driver_lines = []
            slot_labels = {1: "P1", 2: "P2", 3: "RES"}
            for d in sorted(drivers, key=lambda dr: dr.slot or 99):
                slot = slot_labels.get(d.slot, "?")
                ovr = self._calc_driver_ovr(d)
                morale_emoji = self._morale_emoji(d.morale)
                driver_lines.append(
                    f"**{slot}** {d.first_name} {d.last_name}  "
                    f"—  OVR:{ovr:.0f}  {morale_emoji}{d.morale}"
                )
            embed.add_field(
                name=f"👤 Fahrer ({len(drivers)})",
                value="\n".join(driver_lines),
                inline=False,
            )
        else:
            embed.add_field(
                name="👤 Fahrer",
                value="*Keine Fahrer im Team*\n"
                      "Verwende `/driver scout`, um Fahrer zu finden.",
                inline=False,
            )

        # 6. Season stats
        embed.add_field(
            name="🏆 Saison",
            value=(
                f"Punkte: {team.season_points}  ·  "
                f"Siege: {team.wins}  ·  "
                f"Podien: {team.podiums}"
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"Rennen {team.current_race}/14  |  /help für alle Befehle"
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(DashboardCog(bot))
