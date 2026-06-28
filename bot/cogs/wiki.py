"""Wiki cog — guides, wiki overview, and detailed articles for the Motorsport Universe."""

from __future__ import annotations

from typing import Dict

import discord
from discord import app_commands
from discord.ext import commands

# ── Hardcoded guide content ──────────────────────────────────────────────────
# These will be moved to bot/data/guides.py when that module is ready.

GUIDES: Dict[str, Dict[str, str]] = {
    "economy": {
        "title": "💰 Wirtschaft & Budget",
        "emoji": "💰",
        "content": (
            "# Wirtschaft & Budget Guide\n\n"
            "## Einnahmequellen\n"
            "- **Preisgelder**: Pro Rennen basierend auf deiner Liga-Position\n"
            "- **Sponsoren**: `/sponsor` — wähle aus verschiedenen Sponsorenverträgen\n"
            "- **Verkauf**: Verkaufe Fahrer über den Transfermarkt\n\n"
            "## Ausgaben\n"
            "- **Fahrergehälter**: Automatisch abgezogen pro Saison\n"
            "- **Upgrades**: Infrastruktur, Simulator, Aerodynamik\n"
            "- **Scouting**: Academy-Scouts kosten Geld\n\n"
            "## Tipps\n"
            "- Investiere früh in Infrastruktur — das zahlt sich langfristig aus\n"
            "- Wechsle Sponsoren regelmäßig für bessere Deals\n"
            "- Halte immer einen Notgroschen für unerwartete Ausgaben\n\n"
            "## Insolvenz vermeiden\n"
            "Dein Budget darf nicht negativ werden — sonst verlassen dich "
            "Fahrer und du kannst nicht an Rennen teilnehmen."
        ),
    },
    "drivers": {
        "title": "👤 Fahrer & Attribute",
        "emoji": "👤",
        "content": (
            "# Fahrer & Attribute Guide\n\n"
            "## Attribute (0–99)\n"
            "- **Speed**: Maximale Geschwindigkeit\n"
            "- **Consistency**: Weniger Fehler, stabilere Runden\n"
            "- **Racecraft**: Überholmanöver & Verteidigung\n"
            "- **Overtaking**: Erfolgswahrscheinlichkeit bei Überholversuchen\n"
            "- **Tyre Management**: Reifenverschleiß reduzieren\n"
            "- **Qualifying Pace**: Performance im Qualifier\n"
            "- **Wet Performance**: Performance bei Regen\n"
            "- **Mental Strength**: Druckresistenz & Comeback-Fähigkeit\n\n"
            "## Persönlichkeiten\n"
            "- **Calm** 🧘 — Gleichmäßig, selten Fehler\n"
            "- **Aggressive** 🔥 — Maximales Risiko, viele Überholmanöver\n"
            "- **Inconsistent** 🎭 — Mal Weltklasse, mal Katastrophe\n"
            "- **Strategic** 🧠 — Exzellentes Racecraft & Reifenmanagement\n"
            "- **Clutch** 💎 — Liefert unter Druck Höchstleistungen\n\n"
            "## Entwicklung\n"
            "- Fahrer verbessern sich durch Rennen & Training (`/train`)\n"
            "- Jeder Fahrer hat ein verstecktes **Potential** (0–99)\n"
            "- **Growth Rate** bestimmt, wie schnell er sich entwickelt\n"
            "- Ältere Fahrer (>35) bauen langsam ab"
        ),
    },
    "races": {
        "title": "🏁 Rennen & Qualifier",
        "emoji": "🏁",
        "content": (
            "# Rennen & Qualifier Guide\n\n"
            "## Qualifier (`/qualifier run`)\n"
            "1. Jeder deiner Fahrer fährt eine schnelle Runde\n"
            "2. Die Zeiten bestimmen die Startposition im Rennen\n"
            "3. Bessere Startposition = höhere Siegchance\n\n"
            "## Renntag (`/race`)\n"
            "1. Das Rennen wird automatisch simuliert\n"
            "2. Wetter, Reifenstrategie und Fahrerform fließen ein\n"
            "3. Ergebnis: Platzierung, Punkte, Ereignisse\n\n"
            "## Rennereignisse\n"
            "- **Unfälle**: Können zu DNF (Did Not Finish) führen\n"
            "- **Boxenstopps**: Strategie beeinflusst die Zeit\n"
            "- **Safety Car**: Kann das Feld zusammenführen\n"
            "- **Wetterwechsel**: Erfordert flexible Strategie\n\n"
            "## Punktevergabe\n"
            "F1-System: P1=25, P2=18, P3=15, P4=12, P5=10, "
            "P6=8, P7=6, P8=4, P9=2, P10=1"
        ),
    },
    "upgrades": {
        "title": "🔧 Upgrades & Infrastruktur",
        "emoji": "🔧",
        "content": (
            "# Upgrades & Infrastruktur Guide\n\n"
            "## Upgrade-Kategorien\n\n"
            "### 🏢 Infrastruktur\n"
            "- Höheres Level = mehr Einnahmen\n"
            "- Bessere Trainingsmöglichkeiten\n"
            "- Schnellere Fahrerentwicklung\n\n"
            "### 🖥️ Simulator\n"
            "- Verbessert die Lernkurve deiner Fahrer\n"
            "- Reduziert Fehlerquoten im Rennen\n"
            "- Ermöglicht spezielle Trainingsprogramme\n\n"
            "### 🌪️ Aerodynamik\n"
            "- Direkter Einfluss auf Rundenzeiten\n"
            "- Wirkt sich auf Speed & Handling aus\n"
            "- Wichtig für Highspeed-Strecken\n\n"
            "## Upgrade-Kosten\n"
            "Jedes Level kostet mehr als das vorherige. "
            "Plane dein Budget langfristig!\n\n"
            "## Prioritäten\n"
            "1. **Frühe Saison**: Infrastruktur für mehr Einnahmen\n"
            "2. **Mittlere Saison**: Aerodynamik für bessere Ergebnisse\n"
            "3. **Ganze Saison**: Simulator für Fahrerentwicklung"
        ),
    },
    "academy": {
        "title": "🎓 Academy & Fahrerförderung",
        "emoji": "🎓",
        "content": (
            "# Academy & Fahrerförderung Guide\n\n"
            "## Academy-Übersicht (`/academy`)\n"
            "Die Academy ist dein Nachwuchsprogramm. "
            "Hier entdeckst und entwickelst du die nächste Generation "
            "von Motorsport-Stars.\n\n"
            "## Scouting (`/academy scout`)\n"
            "- Finde junge Talente mit hohem Potential\n"
            "- Scouts kosten Geld, aber können sich lohnen\n"
            "- Junge Fahrer haben niedrige Gehälter\n\n"
            "## Training (`/train`)\n"
            "- Trainiere gezielt einzelne Attribute\n"
            "- Academy-Fahrer lernen schneller\n"
            "- Training kostet Zeit & Geld\n\n"
            "## Beförderung\n"
            "Wenn ein Academy-Fahrer gut genug ist, "
            "kannst du ihn ins Hauptteam holen. "
            "Das schafft Platz für neue Talente in der Academy."
        ),
    },
    "ligasystem": {
        "title": "🏆 Liga-System (F1–F10)",
        "emoji": "🏆",
        "content": (
            "# Liga-System Guide (F1–F10)\n\n"
            "## Ligen-Übersicht\n\n"
            "| Liga   | Niveau     | Beschreibung                |\n"
            "|--------|------------|-----------------------------|\n"
            "| F1–F2  | ⭐ Elite   | Höchste Ligen, größte Preise |\n"
            "| F3–F5  | ⭐⭐ Profi  | Mittleres Niveau             |\n"
            "| F6–F8  | ⭐⭐⭐ Semi  | Aufbau-Ligen                 |\n"
            "| F9–F10 | ⭐⭐⭐⭐ Einsteiger | Für neue Teams        |\n\n"
            "## Auf- und Abstieg\n"
            "- **Promotion**: Top 2 Teams steigen eine Liga auf\n"
            "- **Relegation**: Letzte 2 Teams steigen eine Liga ab\n"
            "- In F1 gibt es keine Promotion (höchste Liga)\n"
            "- In F10 gibt es keine Relegation (niedrigste Liga)\n\n"
            "## Vorteile höherer Ligen\n"
            "- Höhere Preisgelder pro Rennen\n"
            "- Bessere Sponsorenverträge\n"
            "- Mehr Prestige & Ansehen\n"
            "- Zugang zu besseren Fahrern auf dem Transfermarkt"
        ),
    },
}

# Ordered list of keys for the select menu
GUIDE_KEYS: list[str] = ["economy", "drivers", "races", "upgrades", "academy", "ligasystem"]

# ── Wiki topics overview ─────────────────────────────────────────────────────

WIKI_CATEGORIES: Dict[str, Dict[str, str | list[str]]] = {
    "Erste Schritte": {
        "emoji": "🚀",
        "color": 0x00FF00,
        "articles": [
            "Wie starte ich?",
            "Die ersten Befehle",
            "Team-Übersicht",
            "Navigation im Menü",
        ],
    },
    "Wirtschaft": {
        "emoji": "💰",
        "color": 0xFFD700,
        "articles": [
            "Einnahmequellen",
            "Sponsoren verwalten",
            "Budget optimieren",
            "Transfermarkt",
            "Preisgelder & Boni",
        ],
    },
    "Fahrer": {
        "emoji": "👤",
        "color": 0x3498DB,
        "articles": [
            "Attribute verstehen",
            "Persönlichkeiten",
            "Training & Entwicklung",
            "Fahrer kaufen & verkaufen",
            "Fahrerverträge",
        ],
    },
    "Rennen": {
        "emoji": "🏁",
        "color": 0xE10600,
        "articles": [
            "Qualifier-Ablauf",
            "Rennsimulation",
            "Wettereinflüsse",
            "Reifenstrategie",
            "DNF & Unfälle",
            "Punkteverteilung",
        ],
    },
    "Academy": {
        "emoji": "🎓",
        "color": 0x00FF00,
        "articles": [
            "Academy einrichten",
            "Scouting-Methoden",
            "Junge Talente fördern",
            "Beförderung ins Hauptteam",
        ],
    },
    "Upgrades": {
        "emoji": "🔧",
        "color": 0xFFD700,
        "articles": [
            "Infrastruktur upgraden",
            "Simulator verbessern",
            "Aerodynamik optimieren",
            "Prioritäten setzen",
        ],
    },
    "Ligen & Saison": {
        "emoji": "🏆",
        "color": 0xE10600,
        "articles": [
            "Ligen-Struktur F1–F10",
            "Auf- und Abstieg",
            "Saisonplanung",
            "Saisonende & Reset",
        ],
    },
    "Premium": {
        "emoji": "⭐",
        "color": 0xFFD700,
        "articles": [
            "Premium-Features",
            "Vorteile",
            "Premium kaufen",
        ],
    },
}


class GuideSelect(discord.ui.Select):
    """Dropdown select menu for choosing a guide topic."""

    def __init__(self) -> None:
        options = []
        for key in GUIDE_KEYS:
            guide = GUIDES[key]
            options.append(
                discord.SelectOption(
                    label=guide["title"],
                    value=key,
                    emoji=guide.get("emoji"),
                )
            )
        super().__init__(
            placeholder="Wähle ein Guide-Thema…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        key = self.values[0]
        guide = GUIDES[key]
        embed = _build_guide_embed(key, guide)
        await interaction.response.edit_message(embed=embed, view=self.view)


class GuideView(discord.ui.View):
    """View wrapping the guide select dropdown."""

    def __init__(self) -> None:
        super().__init__(timeout=180.0)
        self.add_item(GuideSelect())

    async def on_timeout(self) -> None:
        self.stop()


# ── Wiki category view ──────────────────────────────────────────────────────


class WikiCategorySelect(discord.ui.Select):
    """Select menu for wiki categories."""

    def __init__(self) -> None:
        options = []
        for cat_name, cat_data in WIKI_CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=cat_name,
                    value=cat_name,
                    emoji=cat_data["emoji"],  # type: ignore[arg-type]
                )
            )
        super().__init__(
            placeholder="Wähle eine Wiki-Kategorie…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        cat_name = self.values[0]
        cat_data = WIKI_CATEGORIES[cat_name]
        embed = _build_wiki_category_embed(cat_name, cat_data)
        await interaction.response.edit_message(embed=embed, view=self.view)


class WikiCategoryView(discord.ui.View):
    """View wrapping the wiki category select dropdown."""

    def __init__(self) -> None:
        super().__init__(timeout=180.0)
        self.add_item(WikiCategorySelect())

    async def on_timeout(self) -> None:
        self.stop()


# ── Embed builders ──────────────────────────────────────────────────────────


def _build_guide_embed(key: str, guide: dict) -> discord.Embed:
    """Build an embed for a specific guide article."""
    # Choose accent colour based on guide key
    colour_map: Dict[str, int] = {
        "economy": 0xFFD700,
        "drivers": 0x3498DB,
        "races": 0xE10600,
        "upgrades": 0x00FF00,
        "academy": 0x00FF00,
        "ligasystem": 0xE10600,
    }
    colour = colour_map.get(key, 0xE10600)

    embed = discord.Embed(
        title=guide["title"],
        description=guide["content"],
        colour=colour,
    )
    embed.set_footer(text="Motorsport Universe • Guide")
    return embed


def _build_wiki_category_embed(cat_name: str, cat_data: dict) -> discord.Embed:
    """Build an embed showing the articles in a wiki category."""
    articles = cat_data["articles"]  # type: ignore[union-attr]
    colour = cat_data.get("color", 0x3498DB)

    desc_lines = []
    for i, article in enumerate(articles, 1):
        desc_lines.append(f"{i}. **{article}**")

    embed = discord.Embed(
        title=f"{cat_data['emoji']} {cat_name}",
        description="\n".join(desc_lines),
        colour=colour,
    )
    embed.set_footer(
        text="Wähle eine Kategorie aus dem Menü • Nutze /wiki <Thema> für Details"
    )
    return embed


def _build_wiki_overview_embed() -> discord.Embed:
    """Build the main wiki overview embed."""
    embed = discord.Embed(
        title="📚 Motorsport Universe Wiki",
        description=(
            "Willkommen im Wiki! Wähle eine Kategorie aus dem Menü unten, "
            "um zu den entsprechenden Artikeln zu gelangen.\n\n"
            "Du kannst auch direkt `/wiki <Thema>` verwenden, "
            "um einen bestimmten Artikel zu suchen.\n\n"
            "**Verfügbare Kategorien:**"
        ),
        colour=0xE10600,
    )
    for cat_name, cat_data in WIKI_CATEGORIES.items():
        article_count = len(cat_data["articles"])  # type: ignore[arg-type]
        embed.add_field(
            name=f"{cat_data['emoji']} {cat_name}",
            value=f"{article_count} Artikel",
            inline=True,
        )
    embed.set_footer(text="Motorsport Universe • Wiki")
    return embed


# ── Autocomplete ────────────────────────────────────────────────────────────


def _flatten_wiki_articles() -> list[str]:
    """Return all wiki article titles as a flat list."""
    articles: list[str] = []
    for cat_data in WIKI_CATEGORIES.values():
        articles.extend(cat_data["articles"])  # type: ignore[arg-type]
    return articles


async def _wiki_topic_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    all_articles = _flatten_wiki_articles()
    choices = []
    for article in all_articles:
        if current.lower() in article.lower():
            choices.append(app_commands.Choice(name=article, value=article))
    # Return max 25 choices (discord limit)
    return choices[:25]


# ── Cog ─────────────────────────────────────────────────────────────────────


class WikiCog(commands.Cog):
    """Wiki and guide commands for the Motorsport Universe."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── /guide command ──────────────────────────────────────────────────────

    @app_commands.command(
        name="guide",
        description="Zeigt einen Guide zu Wirtschaft, Fahrern, Rennen & mehr",
    )
    async def guide(self, interaction: discord.Interaction) -> None:
        """Show a guide select menu. User picks a topic and sees the guide."""
        embed = discord.Embed(
            title="📖 Guides & Anleitungen",
            description=(
                "Wähle ein Thema aus dem Menü unten, "
                "um den entsprechenden Guide zu sehen."
            ),
            colour=0xE10600,
        )
        embed.set_footer(text="Motorsport Universe • Guides")
        view = GuideView()
        await interaction.response.send_message(embed=embed, view=view)

    # ── /wiki command (no args) ─────────────────────────────────────────────

    @app_commands.command(
        name="wiki",
        description="Zeigt die Wiki-Übersicht oder einen bestimmten Artikel",
    )
    @app_commands.describe(topic="Wiki-Artikel-Thema (optional)")
    @app_commands.autocomplete(topic=_wiki_topic_autocomplete)
    async def wiki(
        self,
        interaction: discord.Interaction,
        topic: str | None = None,
    ) -> None:
        """Show wiki overview or a specific article."""
        if topic is None:
            # Show wiki overview with category select
            embed = _build_wiki_overview_embed()
            view = WikiCategoryView()
            await interaction.response.send_message(embed=embed, view=view)
            return

        # Search for the article across all categories
        found = False
        for cat_name, cat_data in WIKI_CATEGORIES.items():
            for article in cat_data["articles"]:  # type: ignore[union-attr]
                if article.lower() == topic.lower():
                    embed = discord.Embed(
                        title=f"{cat_data['emoji']} {article}",
                        description=(
                            f"*Dieser Artikel gehört zur Kategorie **{cat_name}**.*\n\n"
                            f"Hier findest du detaillierte Informationen zu "
                            f"**{article}** im Motorsport Universe.\n\n"
                            f"Nutze `/guide` für thematische Guides "
                            f"oder `/wiki` für die Kategorie-Übersicht."
                        ),
                        colour=cat_data.get("color", 0x3498DB),
                    )
                    embed.set_footer(
                        text=f"Kategorie: {cat_name} • Motorsport Universe Wiki"
                    )
                    await interaction.response.send_message(embed=embed)
                    found = True
                    break
            if found:
                break

        if not found:
            embed = discord.Embed(
                title="❌ Artikel nicht gefunden",
                description=(
                    f"Der Artikel **„{topic}“** wurde nicht gefunden.\n\n"
                    "Nutze `/wiki` ohne Argumente, um alle Kategorien zu sehen, "
                    "oder `/guide` für thematische Guides."
                ),
                colour=0xE10600,
            )
            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WikiCog(bot))
