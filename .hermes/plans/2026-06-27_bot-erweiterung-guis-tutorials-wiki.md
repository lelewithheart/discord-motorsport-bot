# Discord Motorsport Universe — Bot-Erweiterung

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Vervollständige den Discord Bot mit interaktiven GUIs (Buttons/Selects/Modals), allen fehlenden Commands, Tutorials/Guides und einem Wiki-System.

**Architecture:** 
- **`bot/views/`** — neuer Ordner für Discord UI Components (Paginator, Confirms, Selects)
- **`bot/cogs/`** — bestehende Cogs erweitern + neue `tutorial.py` und `wiki.py` Cogs
- **`bot/embeds.py`** — um Wiki/Guide/Tutorial-Embeds erweitern
- **`bot/data/guides.py`** — Wiki/Guide/Tutorial-Inhalte als Daten

**Tech Stack:** discord.py (app_commands, ui), Python 3.11, sqlite+aiosqlite

---

## Phase 1 — Foundation: UI Components + Help-System

### Task 1: Paginator-Klasse (universal einsetzbar)

**Objective:** Erstelle eine wiederverwendbare Paginator-Klasse mit Buttons (◀️ ▶️ ⏹️) für paginierte Embeds.

**Files:**
- Create: `bot/views/__init__.py`
- Create: `bot/views/paginator.py`

**Code:** `bot/views/paginator.py`
```python
"""Universal paginator for paginated embeds."""
from __future__ import annotations
import discord
from typing import Optional


class Paginator(discord.ui.View):
    """A view that wraps a list of embeds with navigation buttons."""

    def __init__(self, embeds: list[discord.Embed], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current = 0
        self._update_buttons()

    def _update_buttons(self):
        self.first_page.disabled = self.current == 0
        self.prev_page.disabled = self.current == 0
        self.next_page.disabled = self.current >= len(self.embeds) - 1
        self.last_page.disabled = self.current >= len(self.embeds) - 1

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = max(0, self.current - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    @discord.ui.button(label=f"⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_pages(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = min(len(self.embeds) - 1, self.current + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = len(self.embeds) - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    async def on_timeout(self):
        self.stop()
```

**Verification:**
```python
# Post-hoc test: Instantiate Paginator([embed1, embed2, embed3])
# and verify it has 5 buttons, starts at index 0.
```

---

### Task 2: Confirm/Choice-View

**Objective:** Erstelle eine wiederverwendbare ConfirmView (✅ ❌) und ChoiceView (Buttons für Optionen).

**Files:**
- Create: `bot/views/confirm.py`

**Code:** `bot/views/confirm.py`
```python
"""Reusable confirm/cancel and choice views."""
from __future__ import annotations
import discord
from typing import Optional, Callable


class ConfirmView(discord.ui.View):
    """Yes/No confirmation view."""

    def __init__(self, *, timeout: float = 60.0, on_confirm: Optional[Callable] = None,
                 on_cancel: Optional[Callable] = None, user_id: Optional[int] = None):
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id is not None and interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das ist nicht dein Menü!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        if self.on_confirm:
            await self.on_confirm(interaction)
        else:
            await interaction.response.edit_message(view=None)

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        if self.on_cancel:
            await self.on_cancel(interaction)
        else:
            await interaction.response.edit_message(view=None)

    async def on_timeout(self):
        self.stop()


class ChoiceView(discord.ui.View):
    """Multiple choice view with up to 4 buttons in a row."""

    def __init__(self, options: list[tuple[str, str]], *, timeout: float = 60.0,
                 user_id: Optional[int] = None):
        """
        Args:
            options: List of (label, custom_id) tuples. Max 4 buttons.
        """
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.selected: Optional[str] = None
        self.labels: dict[str, str] = {}
        for label, cid in options[:4]:
            self.labels[cid] = label
            self.add_item(ChoiceButton(label=label, custom_id=cid))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id is not None and interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das ist nicht dein Menü!", ephemeral=True)
            return False
        return True


class ChoiceButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str):
        super().__init__(label=label, custom_id=custom_id, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view: ChoiceView = self.view
        view.selected = self.custom_id
        view.stop()
        await interaction.response.edit_message(view=None)
```

---

### Task 3: Interaktives Help-System

**Objective:** Ersetze den statischen `/help` durch einen interaktiven Command-Browser mit Kategorien und Buttons.

**Files:**
- Modify: `bot/cogs/general.py` — Help-Command mit Views
- Modify: `bot/embeds.py` — help_embed mit Kategorie-Embeds

**Implementation:**
1. Erstelle pro Kategorie ein Embed (Rennen, Team, Fahrer, Wirtschaft, Saison, Academy, Ligen)
2. `/help` zeigt Kategorie-Auswahl (Select Menu mit Kategorien)
3. Nach Auswahl wird das passende Embed + Command-Liste angezeigt
4. Buttons: "◀️ Übersicht" und "ℹ️ Command-Details"

---

### Task 4: Interaktive Season Standings

**Objective:** Implementiere `/season_standings` mit DB-Abfrage und Paginator.

**Files:**
- Modify: `bot/cogs/remaining.py` (SeasonCog)

**Implementation:**
```python
@app_commands.command(name="season_standings", description="Saison-Tabelle")
async def season_standings(self, interaction: discord.Interaction):
    await interaction.response.defer()
    async with self.session_maker() as session:
        # Get all teams in same league + season
        team = await TeamRepo.get_by_owner(session, interaction.user.id)
        if not team:
            await interaction.followup.send("❌ Kein Team")
            return
        t = team[0]
        all_teams = await TeamRepo.get_by_league(session, t.league, t.active_season)
    
    # Sort by season_points desc, then wins desc
    sorted_teams = sorted(all_teams, key=lambda x: (-x.season_points, -x.wins))
    
    embeds = []
    for chunk in [sorted_teams[i:i+10] for i in range(0, len(sorted_teams), 10)]:
        embed = discord.Embed(
            title=f"📊 F{t.league} — Saison {t.active_season}",
            colour=0x3498DB,
        )
        lines = []
        for rank, team_entry in enumerate(chunk, 1 + embeds.index(chunk)*10):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
            highlight = "**" if team_entry.id == t.id else ""
            close = "**" if team_entry.id == t.id else ""
            lines.append(
                f"{medal} {highlight}{team_entry.name}{close} — "
                f"{team_entry.season_points} Pkt | {team_entry.wins} S | {team_entry.podiums} P"
            )
        embed.description = "\n".join(lines)
        embeds.append(embed)
    
    if len(embeds) == 1:
        await interaction.followup.send(embed=embeds[0])
    else:
        from bot.views.paginator import Paginator
        await interaction.followup.send(embed=embeds[0], view=Paginator(embeds))
```

---

### Task 5: Markt-System (market + market_buy)

**Objective:** Implementiere `/market` mit Paginator und `/market buy` mit Bestätigung.

**Files:**
- Modify: `bot/cogs/remaining.py` (MarketCog)

**Market changes:**
- `/market` zeigt Free Agents paginiert mit Buttons
- Jeder Eintrag hat eine ID, die man mit `/market buy <id>` kaufen kann
- `/market buy` zeigt ConfirmView vor Kauf
- Nach Kauf: Driver wechselt Team, Embed mit Erfolgsmeldung

---

---

## Phase 2 — Game Systems

### Task 6: Sponsor-System vervollständigen

**Objective:** Implementiere `/sponsor` mit aktuellem Sponsor + Optionen.

**Files:**
- Modify: `bot/cogs/remaining.py` (SponsorCog)
- Modify: `bot/embeds.py` — sponsor_embed

**Implementation:**
```python
def sponsor_embed(team: Team) -> discord.Embed:
    embed = discord.Embed(
        title=f"💰 Sponsoren — {team.name}",
        colour=0xFFD700,
    )
    if team.sponsor_income and team.sponsor_income > 0:
        embed.add_field(name="Aktiver Sponsor", value=f"Einnahmen: ${float(team.sponsor_income):,.0f}/Saison")
    else:
        embed.description = "🔍 Kein Sponsor. Neue Sponsoren werden in der Pre-Season generiert."
    embed.add_field(name="Bonus (Siege)", value=f"${float(team.prize_money or 0):,.0f}")
    embed.add_field(name="Gesamtbudget", value=f"${float(team.budget):,.0f}")
    return embed
```

Der Command ruft Daten aus der DB, erstellt Embed, zeigt ggf. Buttons für "Sponsor kündigen" oder "Verhandeln".

---

### Task 7: Team-Upgrade System

**Objective:** Implementiere `/team_upgrade` mit Auswahl + Kauf.

**Files:**
- Modify: `bot/cogs/team.py` — team_upgrade Command

**Implementation:**
- Select Menu mit verfügbaren Upgrades + Kosten
- Nach Auswahl: ConfirmView
- Bei Bestätigung: Budget prüfen → abziehen → Upgrade-Level erhöhen
- Embed mit Erfolgsmeldung + aktualisierten Stats

---

### Task 8: Academy-System

**Objective:** Implementiere `/academy` und `/academy_scout` mit Scout-UI.

**Files:**
- Modify: `bot/cogs/remaining.py` (AcademyCog)

**Implementation:**
- `/academy` zeigt aktuelle Academy-Fahrer (reserve driver if is_academy) + Scout-Level
- `/academy_scout` zeigt Select Menu mit Regionen (europe, asia, americas, global)
- Nach Auswahl: Generiere Academy-Drops, zeige neue Fahrer

---

## Phase 3 — Tutorials, Guides & Wiki

### Task 9: Tutorial-System

**Objective:** Erstelle `/tutorial` mit geführter Einführung (5 Schritte).

**Files:**
- Create: `bot/cogs/tutorial.py`
- Create: `bot/data/guides.py` (shared content)

**Code:** `bot/data/guides.py`
```python
"""Guide, tutorial and wiki content."""

from typing import NamedDict

TUTORIAL_STEPS = [
    {
        "title": "👋 Willkommen bei Motorsport Universe!",
        "description": (
            "Du bist bereit für die F10-Liga! In diesem Tutorial lernst du die Grundlagen.\n\n"
            "**Was dich erwartet:**\n"
            "• Team-Management\n• Rennen fahren\n• Fahrer entwickeln\n"
            "• Sponsoren & Wirtschaft\n• Aufstieg in höhere Ligen"
        ),
        "buttons": {"✅ Los geht's!"},
    },
    {
        "title": "🏎️ Schritt 1: Team erstellen",
        "description": (
            "Dein erstes Ziel: Erstelle ein Team mit `/team create`!\n\n"
            "Du bekommst:\n"
            "• 2 Hauptfahrer + 1 Reservefahrer\n"
            "• $1,000,000 Startbudget\n"
            "• Einen Einstiegs-Sponsor\n\n"
            "**Tipp:** Dein Team-Name sollte einzigartig sein!"
        ),
        "buttons": {"✅ Team erstellen": "/team_create"},
    },
    ...
]

GUIDES = {
    "economy": {
        "title": "💰 Wirtschafts-Guide",
        "content": (
            "## Einnahmequellen\n\n"
            "**1. Sponsor-Einnahmen** — Dein Hauptsponsor zahlt pro Saison.\n"
            "**2. Preisgeld** — Pro Rennen gibt's Punkte, am Ende Preisgeld.\n"
            "**3. Bonus** — Siege und Podien bringen Extra-Boni.\n\n"
            "## Ausgaben\n\n"
            "**Fahrer-Gehälter** — Basierend auf OVR.\n"
            "**Upgrades** — Aerodynamik, Motor, Simulator.\n"
            "**Scouts** — Academy-Scouts kosten pro Saison."
        ),
    },
    "drivers": {
        "title": "🏎️ Fahrer-Guide",
        "content": (
            "## Fahrer-Attribute (0-100)\n\n"
            "• **Speed** — Maximale Geschwindigkeit\n"
            "• **Consistency** — Gleichmäßige Runden\n"
            "• **Racecraft** — Zweikampf-Verhalten\n"
            "• **Overtaking** — Überholmanöver\n"
            "• **Tyre Management** — Reifenverschleiß\n"
            "• **Qualifying Pace** — Eine Runde Performance\n"
            "• **Wet Performance** — Regenfähigkeiten\n"
            "• **Mental Strength** — Druckresistenz\n\n"
            "## Persönlichkeiten\n\n"
            "Jeder Fahrer hat eine Persönlichkeit, die Boni gibt."
        ),
    },
    "races": {
        "title": "🏁 Renn-Guide",
        "content": (
            "## Renn-Ablauf\n\n"
            "1. **Qualifier** — `/qualifier run` für Startposition\n"
            "2. **Rennen** — `/race` simuliert das Rennen\n"
            "3. **Events** — Zufallsereignisse nach dem Rennen\n\n"
            "## Punktetabelle\n\n"
            "P1: 25 | P2: 18 | P3: 15 | P4: 12 | P5: 10\n"
            "P6: 8 | P7: 6 | P8: 4 | P9: 2 | P10: 1"
        ),
    },
    "upgrades": {
        "title": "🔧 Upgrade-Guide",
        "content": "..."  # Full content
    },
    "academy": {
        "title": "🎓 Academy-Guide",
        "content": "..."  # Full content
    },
    "ligasystem": {
        "title": "🏆 Liga-System",
        "content": "..."  # Full content
    },
}
```

**Tutorial Cog:** `bot/cogs/tutorial.py`
- `/tutorial` — Start der geführten Einführung
- 5 Buttons-Schritte: Willkommen → Team erstellen → Fahrer → Rennen → Nächste Schritte
- Jeder Schritt zeigt ein Embed + Actions

---

### Task 10: Guides & Wiki

**Objective:** Erstelle `/guide` und `/wiki` Commands.

**Files:**
- Create: `bot/cogs/wiki.py`
- Already: `bot/data/guides.py`

**Wiki Cog:** `bot/cogs/wiki.py`
- `/guide` — Select Menu mit Guide-Themen (Economy, Drivers, Races, Upgrades, Academy, Ligasystem)
- `/wiki` — Wiki-Startseite mit Kategorien
- `/wiki <topic>` — Direkt zu einem Thema

---

## Phase 4 — Integration & Deployment

### Task 11: Repository erweitern (fehlende DB-Queries)

**Objective:** Füge fehlende Repository-Methoden hinzu.

**Files:**
- Modify: `src/motorsport/data/repository.py`

**Need to check if these exist:**
- `TeamRepo.get_by_league(session, league, season)` → alle Teams in einer Liga
- `DriverRepo.update_team(session, driver_id, team_id)` → Fahrer-Team wechseln
- `TeamRepo.update(session, team)` → Team speichern

---

### Task 12: Build, Deploy & Test

**Objective:** Baue das Docker-Image neu, deploye und teste alle Commands.

**Steps:**
1. `docker compose build` oder `docker build -t discord-motorsport-universe-bot .`
2. Container stoppen und neustarten
3. Auf Discord testen: `/help`, `/season standings`, `/sponsor`, `/market`, `/tutorial`, `/guide`, `/wiki`, `/team upgrade`

---

## Dateien-Übersicht

| Aktion | Datei | Beschreibung |
|---|---|---|
| Create | `bot/views/__init__.py` | Package init |
| Create | `bot/views/paginator.py` | Paginator-Klasse |
| Create | `bot/views/confirm.py` | Confirm/Choice Views |
| Create | `bot/data/guides.py` | Wiki/Guide/Tutorial Content |
| Create | `bot/cogs/tutorial.py` | Tutorial Cog |
| Create | `bot/cogs/wiki.py` | Wiki & Guide Cog |
| Modify | `bot/cogs/general.py` | Interaktives Help-System |
| Modify | `bot/cogs/team.py` | Upgrade-System |
| Modify | `bot/cogs/remaining.py` | Season Standings, Sponsor, Market, Academy |
| Modify | `bot/embeds.py` | Neue Embed-Builder |
| Modify | `src/motorsport/data/repository.py` | Fehlende Queries |
| Modify | `bot/cogs/__init__.py` | Neue Cogs registrieren |

---

## Risiken & Offene Fragen

- **Repository-Methoden:** Prüfen ob `TeamRepo.get_by_league` existiert; wenn nicht, implementieren.
- **DB-Migration:** Bestehende Teams haben vielleicht keine `sponsor_income` oder `is_academy` Felder — prüfen.
- **Raten-Limits:** Discord erlaubt 5 Interaction-Responses pro Command — Paginator ist safe, aber Modals brauchen 2.
- **Timeout:** Views haben 180s Default-Timeout; bei komplexen Flows ggf. erhöhen.

---

## Execution Plan

1. Task 1 → Paginator
2. Task 2 → Confirm/Choice Views
3. Task 3 → Interaktives Help
4. Task 4 → Season Standings
5. Task 5 → Market System
6. Task 6 → Sponsor System
7. Task 7 → Team Upgrade
8. Task 8 → Academy System
9. Task 9 → Tutorial System
10. Task 10 → Guides & Wiki
11. Task 11 → Repository erweitern
12. Task 12 → Build & Deploy
