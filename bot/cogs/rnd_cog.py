"""R&D commands cog — upgrade components and view the tech tree."""
from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from motorsport.data.database import get_session_maker
from motorsport.data.repository import TeamRepo, RndRepo
from motorsport.systems.rnd import RndManager, RND_COMPONENTS
from bot.views.confirm import ConfirmView
from bot.views.paginator import Paginator


class RndCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _get_user_team(self, session, user_id: int):
        teams = await TeamRepo.get_by_owner(session, user_id)
        return teams[0] if teams else None

    def _get_current_level(self, upgrades: list, component: str) -> int:
        for u in upgrades:
            if u.component == component:
                return u.level
        return 1  # default level

    def _build_progress_bar(self, level: int, max_level: int) -> str:
        filled = min(level, max_level)
        empty = max_level - filled
        return "■" * filled + "□" * empty

    # ── Autocomplete ──────────────────────────────────────────────────────

    async def _component_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []
        for key, comp in RND_COMPONENTS.items():
            label = f"{comp['name']} ({key})"
            if current.lower() in key.lower() or current.lower() in comp['name'].lower():
                choices.append(app_commands.Choice(name=label, value=key))
        return choices[:25]

    # ── /rnd overview ─────────────────────────────────────────────────────

    @app_commands.command(name="rnd", description="R&D Übersicht")
    async def rnd_overview(self, interaction: discord.Interaction):
        """Show R&D overview with points and component levels."""
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send(
                    "❌ Du hast kein Team. Erstelle eines mit `/team_create`"
                )
                return

            rnd_points = await RndRepo.get_points(session, team.id, team.active_season)
            upgrades = await RndRepo.get_upgrades(session, team.id)
            upgrade_dict = {u.component: u.level for u in upgrades}

            bonuses = RndManager.calculate_stat_bonuses(upgrades)

        # Build description
        desc_lines = [
            f"**R&D Punkte:** {rnd_points.points} 💠",
            "*Gesammelt aus Training, Qualifying & Rennen*",
        ]
        if bonuses:
            desc_lines.append("")
            desc_lines.append("**Stat-Boni durch Upgrades:**")
            for stat, bonus in sorted(bonuses.items()):
                desc_lines.append(f"• {stat.title()}: +{int(bonus)}")
        else:
            desc_lines.append("")
            desc_lines.append("*Noch keine Upgrades aktiviert*")

        embed = discord.Embed(
            title="🔬 Research & Development",
            colour=0x9B59B6,
            description="\n".join(desc_lines),
        )

        for key, comp in RND_COMPONENTS.items():
            level = upgrade_dict.get(key, 1)
            max_lv = comp["max_level"]
            cost = RndManager.get_upgrade_cost(key, level)
            bar = self._build_progress_bar(level, max_lv)

            if cost is None:
                cost_str = "✅ MAX"
            else:
                cost_str = f"💠 {cost}"

            embed.add_field(
                name=f"{comp['name']}  {bar}",
                value=f"Lv. {level}/{max_lv}  |  Nächstes: {cost_str}",
                inline=True,
            )

        await interaction.followup.send(embed=embed)

    # ── /rnd upgrade ──────────────────────────────────────────────────────

    @app_commands.command(name="rnd_upgrade", description="R&D Komponente upgraden")
    @app_commands.describe(component="Komponente zum Upgraden")
    @app_commands.autocomplete(component=_component_autocomplete)
    async def rnd_upgrade(
        self, interaction: discord.Interaction, component: str
    ):
        """Upgrade a component. Shows cost, confirm dialog, then applies."""
        # Validate component
        comp_def = RND_COMPONENTS.get(component)
        if not comp_def:
            await interaction.response.send_message(
                f"❌ Unbekannte Komponente: `{component}`. "
                f"Gültige: {', '.join(RND_COMPONENTS.keys())}",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.followup.send("❌ Du hast kein Team.")
                return

            rnd_points = await RndRepo.get_points(session, team.id, team.active_season)
            upgrades = await RndRepo.get_upgrades(session, team.id)
            current_level = self._get_current_level(upgrades, component)
            max_level = comp_def["max_level"]

            # Check max level
            if current_level >= max_level:
                await interaction.followup.send(
                    f"✅ **{comp_def['name']}** hat bereits das Maximallevel "
                    f"(Lv. {max_level}) erreicht!"
                )
                return

            cost = RndManager.get_upgrade_cost(component, current_level)

            # Check points
            if rnd_points.points < cost:
                effects_str = ", ".join(
                    f"{stat.title()}: +{int(per_level)}"
                    for stat, per_level in comp_def["effects"].items()
                )
                embed = discord.Embed(
                    title="❌ Nicht genug R&D Punkte",
                    colour=0xE74C3C,
                    description=(
                        f"**{comp_def['name']}** Lv. {current_level} → {current_level + 1}\n\n"
                        f"Kosten: 💠 **{cost}**\n"
                        f"Du hast: 💠 **{rnd_points.points}**\n\n"
                        f"Fehlen: 💠 **{cost - rnd_points.points}**\n\n"
                        f"*Effekt:* {effects_str}"
                    ),
                )
                await interaction.followup.send(embed=embed)
                return

            # Show confirm dialog
            effects_str = ", ".join(
                f"{stat.title()}: +{int(per_level)}"
                for stat, per_level in comp_def["effects"].items()
            )
            new_bonus = ", ".join(
                f"{stat.title()}: +{int(per_level * current_level)}"
                for stat, per_level in comp_def["effects"].items()
            )

            confirm_embed = discord.Embed(
                title=f"🔬 Upgrade bestätigen — {comp_def['name']}",
                colour=0xF1C40F,
                description=(
                    f"**Level:** {current_level} → **{current_level + 1}** / {max_level}\n"
                    f"**Kosten:** 💠 **{cost}** (Du hast 💠 {rnd_points.points})\n\n"
                    f"**Effekt pro Level:** {effects_str}\n"
                    f"**Neuer Gesamtbonus:** {new_bonus}"
                ),
            )

        view = ConfirmView(
            user_id=interaction.user.id,
            timeout=60.0,
        )

        await interaction.followup.send(embed=confirm_embed, view=view)
        await view.wait()

        if view.value is None:
            # Timeout
            async with self.session_maker() as session:
                team = await self._get_user_team(session, interaction.user.id)
            if team:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="⏰ Upgrade abgelaufen",
                        colour=0x95A5A6,
                        description="Die Bestätigung wurde nicht rechtzeitig gegeben.",
                    ),
                    view=None,
                )
            return

        if not view.value:
            # Cancelled
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Upgrade abgebrochen",
                    colour=0x95A5A6,
                    description=f"Upgrade für **{comp_def['name']}** wurde abgebrochen.",
                ),
                view=None,
            )
            return

        # Confirmed — apply upgrade
        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            if not team:
                await interaction.edit_original_response(
                    content="❌ Team nicht gefunden.", embed=None, view=None
                )
                return

            # Re-check points (in case they changed during dialog)
            rnd_points = await RndRepo.get_points(session, team.id, team.active_season)
            upgrades = await RndRepo.get_upgrades(session, team.id)
            current_level = self._get_current_level(upgrades, component)
            cost = RndManager.get_upgrade_cost(component, current_level)

            if cost is None:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="✅ Bereits max Level",
                        colour=0x2ECC71,
                        description=f"**{comp_def['name']}** ist bereits auf Maximallevel.",
                    ),
                    view=None,
                )
                return

            if rnd_points.points < cost:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Nicht genug R&D Punkte",
                        colour=0xE74C3C,
                        description=(
                            f"Kosten: 💠 {cost} | Du hast: 💠 {rnd_points.points}"
                        ),
                    ),
                    view=None,
                )
                return

            # Deduct points and upgrade
            rnd_points.points -= cost
            upgrade = await RndRepo.upgrade_component(
                session, team.id, component, cost
            )
            await session.commit()

        # Success
        success_embed = discord.Embed(
            title=f"✅ Upgrade erfolgreich — {comp_def['name']}",
            colour=0x2ECC71,
            description=(
                f"**{comp_def['name']}** auf **Level {upgrade.level}**/ {max_level} erhöht!\n"
                f"💠 **{cost}** R&D Punkte ausgegeben.\n"
                f"Verbleibend: 💠 **{rnd_points.points}**"
            ),
        )
        await interaction.edit_original_response(embed=success_embed, view=None)

    # ── /rnd tree ─────────────────────────────────────────────────────────

    @app_commands.command(name="rnd_tree", description="R&D Tech Tree anzeigen")
    async def rnd_tree(self, interaction: discord.Interaction):
        """Show the full R&D tech tree with effects and costs per level."""
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            team = await self._get_user_team(session, interaction.user.id)
            upgrades = []
            if team:
                upgrades = await RndRepo.get_upgrades(session, team.id)
            upgrade_dict = {u.component: u.level for u in upgrades}

        # Build pages — one component per page
        pages: list[discord.Embed] = []
        component_keys = sorted(RND_COMPONENTS.keys())

        for key in component_keys:
            comp = RND_COMPONENTS[key]
            player_level = upgrade_dict.get(key, 1)

            embed = discord.Embed(
                title=f"🔬 {comp['name']}",
                colour=0x9B59B6,
                description=(
                    f"**Komponente:** `{key}`\n"
                    f"**Max Level:** {comp['max_level']}\n"
                    f"**Dein Level:** {player_level}\n\n"
                    f"**Effekte pro Level:**"
                ),
            )

            effects_lines = []
            for stat, per_level in comp["effects"].items():
                total = (player_level - 1) * per_level
                effects_lines.append(
                    f"• {stat.title()}: +{per_level}/Level "
                    f"(aktuell +{int(total)})"
                )
            embed.add_field(
                name="📊 Stat-Effekte",
                value="\n".join(effects_lines) if effects_lines else "—",
                inline=False,
            )

            # Cost table
            cost_lines = []
            for lv in range(1, comp["max_level"] + 1):
                cost = comp["costs"][lv - 1]
                if lv < player_level:
                    icon = "✅"
                elif lv == player_level:
                    icon = "📍"
                else:
                    icon = "🔒"
                cost_lines.append(f"{icon} Lv. {lv} → {lv + 1}: 💠 **{cost}**")

            embed.add_field(
                name="💠 Upgrade-Kosten",
                value="\n".join(cost_lines),
                inline=False,
            )

            embed.set_footer(
                text=f"{component_keys.index(key) + 1}/{len(component_keys)}"
                f" | ✅ besitzt du | 📍 aktuell | 🔒 noch offen"
            )
            pages.append(embed)

        if not pages:
            await interaction.followup.send("❌ Keine Komponenten gefunden.")
            return

        if len(pages) == 1:
            await interaction.followup.send(embed=pages[0])
            return

        view = Paginator(
            pages=pages,
            user_id=interaction.user.id if team else None,
            timeout=180.0,
        )
        await interaction.followup.send(embed=pages[0], view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(RndCog(bot))
