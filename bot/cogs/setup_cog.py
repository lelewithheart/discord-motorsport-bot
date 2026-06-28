"""Setup commands cog — configure car setups for each track."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.data.database import get_session_maker
from motorsport.data.repository import SetupRepo, TrackRepo, RaceScheduleRepo, TeamRepo
from motorsport.systems.setup import SetupCalculator
from motorsport.data.models import SetupModel

SETUP_PARAMS = {
    "front_wing": "Frontflügel — Abtrieb vs. Speed",
    "rear_wing": "Heckflügel — Stabilität vs. Speed",
    "suspension": "Aufhängung — weich=Reifen, hart=Bremsen",
    "gear_ratio": "Getriebe — kurz=Accel, lang=Speed",
    "tire_compound": "Reifen — weich=Grip, hart=Haltbarkeit",
}


def _setup_bar(value: int) -> str:
    filled = max(1, min(10, value // 2))
    empty = 10 - filled
    return "🟦" * filled + "⬜" * empty


def _setup_to_embed(
    title: str,
    setup: SetupModel,
    track: TrackModel | None = None,
    colour: int = 0x3498DB,
    footer: str | None = None,
) -> discord.Embed:
    description = f"**Name:** {setup.name}"
    if track:
        description += f"\n**Track:** {track.name} ({track.country or '—'})"

    embed = discord.Embed(title=title, colour=colour, description=description)

    for key, hint in SETUP_PARAMS.items():
        val = getattr(setup, key)
        bar = _setup_bar(val)
        embed.add_field(
            name=key.replace("_", " ").title(),
            value=f"{bar} {val}/20 — {hint}",
            inline=False,
        )

    if footer:
        embed.set_footer(text=footer)
    return embed


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    # ── helpers ──────────────────────────────────────────────────────────

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
                return await TrackRepo.get_by_id(session, s.track_id)
        return None

    async def _get_user_team(self, session, user_id: int):
        teams = await TeamRepo.get_by_owner(session, user_id)
        return teams[0] if teams else None

    async def _get_active_setup(self, session, team, track: TrackModel | None):
        """Return (setup, is_track_specific) tuple."""
        if track:
            track_setups = await SetupRepo.get_by_track(session, team.id, track.id)
            if track_setups:
                return track_setups[0], True

        default = await SetupRepo.get_default(session, team.id)
        if default:
            return default, False

        # Fallback: create a default setup
        setup = await SetupRepo.create(session, team.id, "Default", track_id=None)
        return setup, False

    async def _setup_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                return []
            setups = await SetupRepo.get_by_team(session, team.id)
        choices = []
        for s in setups:
            if current.lower() in s.name.lower():
                choices.append(app_commands.Choice(name=s.name, value=s.id))
        return choices[:25]

    async def _param_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        valid = list(SETUP_PARAMS.keys())
        choices = []
        for p in valid:
            if current.lower() in p.lower():
                choices.append(
                    app_commands.Choice(name=SETUP_PARAMS[p].split(" — ")[0], value=p)
                )
        return choices[:25]

    # ── /setup group ────────────────────────────────────────────────────

    setup = app_commands.Group(name="setup", description="Car setup management")

    @setup.command(name="show", description="Show current active setup")
    async def setup_show(self, interaction: discord.Interaction):
        """Show current setup for the current/next race track."""
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team. Erstelle eines mit `/team_create`")
                return

            track = await self._get_current_track(session, team)
            setup, is_track_specific = await self._get_active_setup(session, team, track)

        title = f"🔧 Setup — {track.name if track else 'Default'}"
        rec_footer = None
        if track:
            rec = SetupCalculator.recommend_setup(track)
            rec_footer = (
                f"💡 Empfohlen: FW={rec['front_wing']} RW={rec['rear_wing']} "
                f"S={rec['suspension']} G={rec['gear_ratio']} R={rec['tire_compound']}"
            )

        embed = _setup_to_embed(title, setup, track, footer=rec_footer)
        await interaction.followup.send(embed=embed)

    @setup.command(name="adjust", description="Adjust a setup parameter")
    @app_commands.describe(
        param="Parameter to adjust (front_wing, rear_wing, suspension, gear_ratio, tire_compound)",
        value="New value (1-20)",
    )
    @app_commands.autocomplete(param=_param_autocomplete)
    async def setup_adjust(
        self, interaction: discord.Interaction, param: str, value: int
    ):
        if param not in SETUP_PARAMS:
            await interaction.response.send_message(
                f"❌ Ungültiger Parameter. Gültige: {', '.join(SETUP_PARAMS.keys())}",
                ephemeral=True,
            )
            return
        if not 1 <= value <= 20:
            await interaction.response.send_message(
                "❌ Wert muss zwischen 1 und 20 liegen.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            track = await self._get_current_track(session, team)
            setup, _ = await self._get_active_setup(session, team, track)

            # Update the parameter
            setattr(setup, param, value)
            await SetupRepo.update(session, setup)

        embed = _setup_to_embed(
            f"✅ Setup angepasst — {param.replace('_', ' ').title()} = {value}",
            setup,
            track,
            colour=0x00FF00,
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name="save", description="Save current setup with a name")
    @app_commands.describe(name="Name for this setup preset")
    async def setup_save(self, interaction: discord.Interaction, name: str):
        if len(name) > 64:
            await interaction.response.send_message(
                "❌ Name darf maximal 64 Zeichen lang sein.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            track = await self._get_current_track(session, team)
            setup, _ = await self._get_active_setup(session, team, track)

            # Create a copy of the current setup as a named save
            new_setup = await SetupRepo.create(
                session,
                team.id,
                name=name,
                track_id=track.id if track else None,
                front_wing=setup.front_wing,
                rear_wing=setup.rear_wing,
                suspension=setup.suspension,
                gear_ratio=setup.gear_ratio,
                tire_compound=setup.tire_compound,
            )

        await interaction.followup.send(
            f"✅ Setup **{name}** gespeichert für "
            f"{'Track: ' + track.name if track else 'Default'}."
        )

    @setup.command(name="load", description="Load a saved setup by name")
    @app_commands.describe(name="Setup name to load")
    @app_commands.autocomplete(name=_setup_name_autocomplete)
    async def setup_load(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            setup = await SetupRepo.get(session, name)
            if not setup or setup.team_id != team.id:
                await interaction.followup.send("❌ Setup nicht gefunden.")
                return

            track = await TrackRepo.get_by_id(session, setup.track_id) if setup.track_id else None

        embed = _setup_to_embed(
            f"📂 Setup geladen — {setup.name}",
            setup,
            track,
            colour=0x3498DB,
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name="list", description="List all saved setups")
    async def setup_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            setups = await SetupRepo.get_by_team(session, team.id)

        if not setups:
            await interaction.followup.send("📭 Keine gespeicherten Setups gefunden.")
            return

        embed = discord.Embed(
            title=f"📋 Setups — {team.name}",
            colour=0x3498DB,
            description=f"{len(setups)} Setup{'s' if len(setups) != 1 else ''} gespeichert",
        )

        # Group by track
        track_setups: dict[str | None, list[SetupModel]] = {}
        for s in setups:
            track_setups.setdefault(s.track_id, []).append(s)

        async with self.session_maker() as session:
            for track_id, group in track_setups.items():
                track_name = "Default/Kein Track"
                if track_id:
                    t = await TrackRepo.get_by_id(session, track_id)
                    if t:
                        track_name = t.name
                lines = []
                for s in group:
                    star = "⭐ " if s.is_default else ""
                    lines.append(
                        f"{star}**{s.name}** — FW={s.front_wing} RW={s.rear_wing} "
                        f"S={s.suspension} G={s.gear_ratio} R={s.tire_compound}"
                    )
                embed.add_field(
                    name=f"📍 {track_name}",
                    value="\n".join(lines) if lines else "—",
                    inline=False,
                )

        await interaction.followup.send(embed=embed)

    @setup.command(name="default", description="Set a saved setup as default")
    @app_commands.describe(name="Setup name to set as default")
    @app_commands.autocomplete(name=_setup_name_autocomplete)
    async def setup_default(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            setup = await SetupRepo.get(session, name)
            if not setup or setup.team_id != team.id:
                await interaction.followup.send("❌ Setup nicht gefunden.")
                return

            await SetupRepo.set_default(session, team.id, setup.id)

        await interaction.followup.send(f"✅ **{setup.name}** ist jetzt das Standard-Setup.")

    @setup.command(name="recommend", description="Show recommended setup for current track")
    async def setup_recommend(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            track = await self._get_current_track(session, team)
            if not track:
                await interaction.followup.send("❌ Kein aktuelles Rennwochenende gefunden.")
                return

            rec = SetupCalculator.recommend_setup(track)

        embed = discord.Embed(
            title=f"💡 Empfohlenes Setup — {track.name}",
            colour=0x9B59B6,
            description=(
                f"Basierend auf den Anforderungen der Strecke:\n"
                f"**Speed:** {track.req_speed:.0%} | **Acceleration:** {track.req_acceleration:.0%}\n"
                f"**Downforce:** {track.req_downforce:.0%} | **Braking:** {track.req_braking:.0%}\n"
                f"**Tyre Management:** {track.req_tyre_management:.0%}"
            ),
        )

        param_labels = {
            "front_wing": "Frontflügel",
            "rear_wing": "Heckflügel",
            "suspension": "Aufhängung",
            "gear_ratio": "Getriebe",
            "tire_compound": "Reifen",
        }

        for key, label in param_labels.items():
            val = rec[key]
            bar = _setup_bar(val)
            embed.add_field(name=label, value=f"{bar} {val}/20", inline=True)

        embed.set_footer(text="Nutze /setup adjust, um Parameter anzupassen")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
