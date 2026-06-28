"""General commands cog — interactive help, about, premium, etc."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from bot.embeds import help_embed, command_detail_embed, _COMMAND_DETAILS


class HelpSelect(discord.ui.Select):
    """Dropdown select menu for choosing a help category."""

    def __init__(self, user_id: int) -> None:
        self._user_id = user_id
        options = []
        for cat_name in _COMMAND_DETAILS:
            # Extract emoji prefix from category name
            emoji = cat_name.split()[0] if cat_name else None
            options.append(
                discord.SelectOption(
                    label=cat_name,
                    value=cat_name,
                    emoji=emoji,
                )
            )
        super().__init__(
            placeholder="Wähle eine Kategorie…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # User-lock: only the command author can use this
        if interaction.user.id != self._user_id:
            await interaction.response.send_message(
                "❌ Diese Hilfe gehört einem anderen Spieler.", ephemeral=True
            )
            return

        await interaction.response.defer()
        category = self.values[0]
        commands = _COMMAND_DETAILS[category]
        embed = command_detail_embed(category, commands)
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embed=embed,
            view=self.view,
        )


class HelpView(discord.ui.View):
    """View wrapping the help category select dropdown."""

    def __init__(self, user_id: int, *, timeout: float = 180.0) -> None:
        super().__init__(timeout=timeout)
        self.add_item(HelpSelect(user_id=user_id))

    async def on_timeout(self) -> None:
        # Disable all children on timeout
        for child in self.children:
            child.disabled = True
        self.stop()


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Zeigt alle Befehle an — interaktive Kategorie-Auswahl")
    async def help_cmd(self, interaction: discord.Interaction):
        """Send an interactive help embed with a category dropdown."""
        embed = help_embed()
        view = HelpView(user_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="commands", description="Alias für /help — zeigt alle Befehle an")
    async def commands_cmd(self, interaction: discord.Interaction):
        """Alias for /help — same interactive experience."""
        embed = help_embed()
        view = HelpView(user_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="about", description="Info über das Spiel")
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏁 Discord Motorsport Universe",
            colour=0xE10600,
            description=(
                "Ein skalierbares Multiplayer-Motorsport-Management-System.\n\n"
                "**Features:**\n"
                "• 10 Offizielle Ligen (F1-F10)\n"
                "• Prozedurale Fahrer-Generierung\n"
                "• Dynamisches Wetter & Events\n"
                "• Sponsor-System\n"
                "• Academy & Scouting\n"
                "• Promotion/Relegation\n\n"
                "**Kein Pay-to-Win** — Premium nur für Komfort & Erweiterung\n\n"
                "Powered by Hermes Agent"
            )
        )
        embed.set_footer(text="Version 1.0.0")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="premium", description="Premium-Infos")
    async def premium(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⭐ Premium",
            colour=0xFFD700,
            description="**5–10€/Monat** — Kein Pay-to-Win, nur Komfort!",
        )
        embed.add_field(name="Free", value=(
            "• 1 Team\n"
            "• Basis-Analytics\n"
            "• 1 Training/Woche\n"
            "• Letzte Saison History"
        ), inline=True)
        embed.add_field(name="Premium", value=(
            "• 3–5 Teams\n"
            "• Detaillierte Analytics\n"
            "• 3 Training/Woche\n"
            "• Alle Seasons\n"
            "• 2× Simulationsgeschw."
        ), inline=True)
        embed.add_field(name="Optional", value=(
            "• Extra Team Slot: 3€\n"
            "• Custom Branding: 5€\n"
            "• Season Pass: 8€\n"
            "• Private Liga: 15€/Monat"
        ), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="premium_status", description="Dein Premium-Status")
    async def premium_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⭐ Premium Status",
            colour=0x3498DB,
        )
        embed.add_field(name="Status", value="🔓 Free Tier (Premium-Features gesperrt)")
        embed.add_field(name="Teams", value="1/1 genutzt")
        embed.set_footer(text="Premium ab 5€/Monat — /premium")
        await interaction.response.send_message(embed=embed, ephemeral=True)
