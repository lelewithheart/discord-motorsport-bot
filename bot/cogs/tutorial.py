"""Tutorial cog — interactive 5-step guided tutorial for new players."""

from __future__ import annotations

from typing import List

import discord
from discord import app_commands
from discord.ext import commands

# ── Hardcoded tutorial steps ──────────────────────────────────────────────────
# These will be moved to bot/data/guides.py when that module is ready.

TUTORIAL_STEPS: List[dict] = [
    {
        "title": "👋 Willkommen im Motorsport Universe",
        "description": (
            "Du übernimmst ein Team in einer der 10 Ligen (F1–F10). "
            "Dein Ziel: Fahre schnelle Runden, entwickle Fahrer, "
            "manage dein Budget und steige bis in die Königsklasse auf.\n\n"
            "**So startest du:**\n"
            "• Nutze `/menu` — dort findest du alle wichtigen Befehle\n"
            "• Mit `/help` bekommst du eine Übersicht aller Commands\n"
            "• `/about` zeigt dir die Spiel-Infos\n\n"
            "**Tipp:** Lerne erst die Basics, dann tauche tiefer ein!"
        ),
    },
    {
        "title": "🏎️ Team erstellen & verwalten",
        "description": (
            "Dein Team ist das Herzstück deines Spiels.\n\n"
            "**Erstellung:**\n"
            "• `/team create <Name>` — gründe dein Team\n"
            "• Wähle einen einzigartigen Namen\n\n"
            "**Verwaltung:**\n"
            "• `/team` — Übersicht über dein Team\n"
            "• `/team upgrade` — Verbessere Infrastruktur & Co.\n"
            "• Jedes Team hat ein Budget für Fahrer, Upgrades & mehr\n\n"
            "**Tipp:** Ein guter Teamname bringt Bonus-Prestige! 🏆"
        ),
    },
    {
        "title": "👤 Fahrer verstehen & managen",
        "description": (
            "Fahrer sind dein wichtigstes Kapital.\n\n"
            "**Attribute (0–99):**\n"
            "• Speed • Consistency • Racecraft • Overtaking\n"
            "• Tyre Management • Qualifying Pace\n"
            "• Wet Performance • Mental Strength\n\n"
            "**Fahrer finden:**\n"
            "• `/market` — Kaufe Fahrer auf dem Transfermarkt\n"
            "• `/academy scout` — Entdecke junge Talente\n"
            "• Jeder Fahrer hat eine einzigartige Persönlichkeit\n\n"
            "**Tipp:** Ein ausgeglichenes Fahrerduo schlägt oft zwei Stars!"
        ),
    },
    {
        "title": "⏱️ Qualifier & Rennen",
        "description": (
            "So funktioniert ein Rennwochenende:\n\n"
            "**1. Qualifier (`/qualifier run`)**\n"
            "• Jeder Fahrer fährt eine schnelle Runde\n"
            "• Die Zeiten bestimmen die Startaufstellung\n\n"
            "**2. Rennen (`/race`)**\n"
            "• Automatische Simulation mit Wetter & Strategie\n"
            "• Punkte für Team- und Fahrerwertung\n"
            "• Safety Car, Unfälle & Boxenstopps möglich\n\n"
            "**Tipp:** Ein guter Qualifier ist die halbe Miete! 🏁"
        ),
    },
    {
        "title": "📈 Nächste Schritte & Tipps",
        "description": (
            "Du hast die Basics gelernt — jetzt geht's los!\n\n"
            "**Empfohlene nächste Schritte:**\n"
            "1. Team erstellen → `/team create <Name>`\n"
            "2. Fahrer kaufen → `/market`\n"
            "3. Upgrades erforschen → `/guide`\n"
            "4. Erstes Rennen → `/qualifier run` + `/race`\n\n"
            "**Profi-Tipps:**\n"
            "• Investiere früh in Infrastruktur 🏢\n"
            "• Wechsle Sponsoren regelmäßig 💰\n"
            "• Trainiere deine Fahrer wöchentlich 🏋️\n"
            "• Nutze `/wiki` für detaillierte Artikel\n\n"
            "**Viel Erfolg auf der Strecke!** 🏆"
        ),
    },
]


class TutorialView(discord.ui.View):
    """Navigation view for the tutorial steps — back/forward buttons."""

    def __init__(self, pages: List[discord.Embed], user_id: int) -> None:
        super().__init__(timeout=180.0)
        self.pages = pages
        self.current = 0
        self.user_id = user_id
        self._update_buttons()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _check_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id != self.user_id

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.current == 0
        self.next_btn.disabled = self.current == len(self.pages) - 1

    async def _navigate(self, interaction: discord.Interaction, delta: int) -> None:
        if self._check_user(interaction):
            await interaction.response.send_message(
                "Diese Navigation gehört einem anderen Spieler.", ephemeral=True
            )
            return
        self.current = max(0, min(len(self.pages) - 1, self.current + delta))
        self._update_buttons()
        embed = self.pages[self.current]
        embed.set_footer(text=f"Schritt {self.current + 1} von {len(self.pages)}")
        await interaction.response.edit_message(embed=embed, view=self)

    # ── Buttons ─────────────────────────────────────────────────────────────

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="tutorial_prev")
    async def prev_btn(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        await self._navigate(interaction, -1)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="tutorial_stop")
    async def stop_btn(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        if self._check_user(interaction):
            await interaction.response.send_message(
                "Diese Navigation gehört einem anderen Spieler.", ephemeral=True
            )
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="tutorial_next")
    async def next_btn(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        await self._navigate(interaction, 1)

    async def on_timeout(self) -> None:
        self.stop()


class TutorialCog(commands.Cog):
    """Interactive tutorial for new players."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tutorial",
        description="Starte eine interaktive 5-Schritt Tutorial-Tour",
    )
    async def tutorial(self, interaction: discord.Interaction) -> None:
        """Start the interactive guided tutorial."""
        pages = []
        for i, step in enumerate(TUTORIAL_STEPS):
            embed = discord.Embed(
                title=step["title"],
                description=step["description"],
                colour=0xE10600,
            )
            embed.set_footer(text=f"Schritt {i + 1} von {len(TUTORIAL_STEPS)}")
            pages.append(embed)

        view = TutorialView(pages=pages, user_id=interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TutorialCog(bot))
