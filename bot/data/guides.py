"""Guide, tutorial and wiki data for the Motorsport Universe bot."""

from __future__ import annotations

from typing import Dict, List

# ─── Tutorial Steps ──────────────────────────────────────────────────────────

TUTORIAL_STEPS: List[Dict[str, str]] = [
    {
        "title": "👋 Willkommen im Motorsport Universe",
        "description": (
            "Du übernimmst ein Team in einer der 10 Ligen (F1–F10). "
            "Dein Ziel: Fahre schnelle Runden, entwickle Fahrer, "
            "manage dein Budget und steige bis in die Königsklasse auf.\n\n"
            "Starte mit `/menu` — dort findest du alle wichtigen Befehle.\n"
            "Nutze `/help` für eine Übersicht aller Commands."
        ),
    },
    {
        "title": "🏎️ Dein Team & Fahrer",
        "description": (
            "Mit `/team` siehst du dein aktuelles Team, die Fahrer, "
            "Budget und Performance-Werte.\n\n"
            "Jeder Fahrer hat 8 Attribute (z. B. Speed, Consistency, "
            "Racecraft) und eine Persönlichkeit, die sein Fahrverhalten "
            "beeinflusst.\n\n"
            "Du kannst Fahrer über `/market` kaufen oder über "
            "`/academy scout` junge Talente entdecken."
        ),
    },
    {
        "title": "⏱️ Qualifier & Rennen",
        "description": (
            "Vor jedem Rennen läuft ein **Qualifier** (`/qualifier run`). "
            "Deine Fahrer fahren eine schnelle Runde — "
            "die Zeiten bestimmen die Startaufstellung.\n\n"
            "Danach startet das Rennen (`/race`). "
            "Wetter, Reifenstrategie und Fahrerform beeinflussen "
            "das Ergebnis. Punkte gibt's für die Team- und Fahrerwertung."
        ),
    },
    {
        "title": "📈 Upgrades & Academy",
        "description": (
            "Verbessere dein Team mit `/team upgrade`:\n"
            "• **Infrastruktur** — höheres Level = mehr Einnahmen & bessere Entwicklung\n"
            "• **Simulator** — schnellere Fahrer-Progression\n"
            "• **Aerodynamik** — bessere Rundenzeiten\n\n"
            "In der **Academy** (`/academy`) kannst du:\n"
            "• Junge Fahrer scouten (`/academy scout`)\n"
            "• Fahrer trainieren (`/train`)\n"
            "• Talente fördern und später ins Hauptteam holen"
        ),
    },
    {
        "title": "🏆 Ligen & Wirtschaft",
        "description": (
            "Die Ligen F1–F10 sind hierarchisch:\n"
            "• Die Top-2 Teams steigen auf (Promotion)\n"
            "• Die letzten 2 Teams steigen ab (Relegation)\n\n"
            "**Wirtschaft:**\n"
            "• Sponsoren (`/sponsor`) bringen passives Einkommen\n"
            "• Fahrer verlassen dich bei zu niedrigem Budget\n"
            "• Größere Ligen = höhere Preisgelder\n\n"
            "Viel Erfolg — und jetzt leg los!"
        ),
    },
]

# ─── Guides ──────────────────────────────────────────────────────────────────

GUIDES: Dict[str, Dict[str, str]] = {
    "economy": {
        "title": "💰 Wirtschaft & Budget",
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
            "- Fahrer verbessern sich durch Rennen & Training `/train`\n"
            "- Jeder Fahrer hat ein verstecktes **Potential** (0–99)\n"
            "- **Growth Rate** bestimmt, wie schnell er sich entwickelt\n"
            "- Ältere Fahrer (>35) bauen langsam ab"
        ),
    },
    "races": {
        "title": "🏁 Rennen & Qualifier",
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

# ─── Wiki Topics ─────────────────────────────────────────────────────────────

WIKI_TOPICS: Dict[str, List[str]] = {
    "Erste Schritte": [
        "Wie starte ich?",
        "Die ersten Befehle",
        "Team-Übersicht",
        "Navigation im Menü",
    ],
    "Wirtschaft": [
        "Einnahmequellen",
        "Sponsoren verwalten",
        "Budget optimieren",
        "Transfermarkt",
        "Preisgelder & Boni",
    ],
    "Fahrer": [
        "Attribute verstehen",
        "Persönlichkeiten",
        "Training & Entwicklung",
        "Fahrer kaufen & verkaufen",
        "Fahrerverträge",
    ],
    "Rennen": [
        "Qualifier-Ablauf",
        "Rennsimulation",
        "Wettereinflüsse",
        "Reifenstrategie",
        "DNF & Unfälle",
        "Punkteverteilung",
    ],
    "Academy": [
        "Academy einrichten",
        "Scouting-Methoden",
        "Junge Talente fördern",
        "Beförderung ins Hauptteam",
    ],
    "Upgrades": [
        "Infrastruktur upgraden",
        "Simulator verbessern",
        "Aerodynamik optimieren",
        "Prioritäten setzen",
    ],
    "Ligen & Saison": [
        "Ligen-Struktur F1–F10",
        "Auf- und Abstieg",
        "Saisonplanung",
        "Saisonende & Reset",
    ],
    "Premium": [
        "Premium-Features",
        "Vorteile",
        "Premium kaufen",
    ],
}
