"""General commands cog — help, about, etc."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from bot.embeds import help_embed


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Zeigt alle Befehle an")
    async def help_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=help_embed())

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
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="premium_status", description="Dein Premium-Status")
    async def premium_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⭐ Premium Status",
            colour=0x3498DB,
        )
        embed.add_field(name="Status", value="🔓 Free Tier (Premium-Features gesperrt)")
        embed.add_field(name="Teams", value="1/1 genutzt")
        embed.set_footer(text="Premium ab 5€/Monat — /premium")
        await interaction.response.send_message(embed=embed)
