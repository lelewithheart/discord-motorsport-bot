# DISCORD MOTORSPORT UNIVERSE — Game Design Document

> **Version:** 1.0  
> **Autor:** Game Design & System Architecture  
> **Plattform:** Discord Bot (Python, discord.py)  
> **Status:** Design Spec

---

## Inhaltsverzeichnis

1. [System Overview](#1-system-overview)
2. [Core Game Loop](#2-core-game-loop)
3. [Race & Qualifying System](#3-race--qualifying-system)
4. [Procedural Driver System](#4-procedural-driver-system)
5. [Name Generation System](#5-name-generation-system)
6. [Team System](#6-team-system)
7. [Sponsor System](#7-sponsor-system)
8. [Academy System](#8-academy-system)
9. [Season Structure](#9-season-structure)
10. [Monetarisierung](#10-monetarisierung)
11. [Discord Integration](#11-discord-integration)
12. [Technical Architecture](#12-technical-architecture)
13. [Database Schema](#13-database-schema)
14. [Simulation Engine Spec](#14-simulation-engine-spec)
15. [State Machine & Event System](#15-state-machine--event-system)
16. [Ranking & Elo Integration](#16-ranking--elo-integration)

---

## 1. SYSTEM OVERVIEW

Das Spiel besteht aus zwei vollständig getrennten, aber verzahnten Ebenen.

```
┌─────────────────────────────────────────────────────┐
│              DISCORD MOTORSPORT UNIVERSE             │
├──────────────────────┬──────────────────────────────┤
│   OFFLINE UNIVERSE   │     ONLINE LIGA SYSTEM       │
│   (Simulation Layer) │     (Competitive Layer)       │
├──────────────────────┼──────────────────────────────┤
│ Jeder Spieler hat    │ 10 offizielle Ligen:          │
│ SEIN eigenes         │ F1 (Top) → F10 (Beginner)    │
│ Universum.           │ Je 10 Teams = 100 Teams max  │
│                      │                              │
│ • Rennen simulieren  │ • Qualifier-Wettbewerb       │
│ • Fahrer entwickeln  │ • Auf-/Abstieg               │
│ • Teams wachsen      │ • Globale Rangliste          │
│ • Sponsoren + Budget │                              │
│ • Dynamische Events  │                              │
└──────────────────────┴──────────────────────────────┘
```

### 1.1 Offline Universe (Simulation Layer)

**Jeder Spieler besitzt sein eigenes, isoliertes Universum.**

- Rennen werden simuliert (deterministisch via Seed)
- Fahrer entwickeln sich über Seasons
- Teams wachsen oder fallen
- Sponsoren generieren Einkommen
- Dynamische Ereignisse (Unfälle, Durchbrüche, Skandale)
- **Nicht direkt kompetitiv** — dient als Basis für den Online-Teil

### 1.2 Online League System (Competitive Layer)

**10 Ligen mit globalem Wettbewerb.**

| Liga | Skill-Level | Teams | Qualifier-Penalty |
|------|-------------|-------|-------------------|
| F1   | Legendär    | 10    | +1.5s             |
| F2   | Elite       | 10    | +1.8s             |
| F3   | Profi       | 10    | +2.0s             |
| F4   | Semi-Pro    | 10    | +2.3s             |
| F5   | Fortgeschritten | 10 | +2.7s             |
| F6   | Mittel       | 10    | +3.0s             |
| F7   | Aufsteigend  | 10    | +3.5s             |
| F8   | Entwickelnd  | 10    | +4.0s             |
| F9   | Anfänger     | 10    | +4.5s             |
| F10  | Einstieg     | 10    | +5.0s             |

**100 Teams insgesamt. Keine Aufstockung möglich — echte Knappheit.**

---

## 2. CORE GAME LOOP

```
┌──────────────────────────────────────────────────────────┐
│                     SEASON CYCLE                         │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐          │
│  │ PRE-     │───→│ SEASON   │───→│ POST-     │          │
│  │ SEASON   │    │ (Rennen  │    │ SEASON    │          │
│  │          │    │  + Qual) │    │           │          │
│  └──────────┘    └──────────┘    └───────────┘          │
│       │               │               │                  │
│       ▼               ▼               ▼                  │
│  • Transfers    • 12-24 Rennen   • Ranking              │
│  • Sponsoren    • Qualifier      • Promotion/Relegation │
│  • Training     • Entwicklung    • Academy Drop         │
│  • Academy      • Events         • Budget Reset         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2.1 Phase 1: Offline Season Simulation

Der Spieler managt sein Team über eine Saison (12–24 Rennen).

**Pro Rennen:**
1. Team-Aufstellung wählen (2 Hauptfahrer + 1 Reserve)
2. Strategie setzen (Aggressiv, Ausgeglichen, Konservativ)
3. Rennen wird simuliert (Ergebnis + Ereignisse)
4. Fahrer-Entwicklung aktualisiert
5. Budget aktualisiert (Sponsoren, Preisgelder, Kosten)

### 2.2 Phase 2: Qualifier System (während der Saison)

**Nach jedem Offline-Rennen** findet ein Online-Qualifier statt.

**Regeln:**
- Jedes Team stellt **3 Fahrer** (2 Haupt + 1 Reserve)
- Jeder Fahrer fährt **1 Runde** (simuliert)
- **Teamwert = Durchschnitt der 3 Zeiten**
- Optional: Best 2 of 3 System

```
Team Qualifier Score = (LapTime_F1 + LapTime_F2 + LapTime_F3) / 3
```

**Die Qualifier-Zeit wird mit dem Fahrzeug aus dem Offline-Universum berechnet — kein separates Setup.**

### 2.3 Phase 3: Standardzeit System (Anti-AFK)

Wenn ein Team nicht am Qualifier teilnimmt:

```
Standardzeit = Liga_Median + Liga_Penalty
```

| Liga  | Penalty |
|-------|---------|
| F1    | +1.5s   |
| F2    | +1.8s   |
| F3    | +2.0s   |
| F4    | +2.3s   |
| F5    | +2.7s   |
| F6    | +3.0s   |
| F7    | +3.5s   |
| F8    | +4.0s   |
| F9    | +4.5s   |
| F10   | +5.0s   |

**Wiederholtes AFK:** Nach 3 aufeinanderfolgenden verpassten Qualifiern → automatischer Abstieg in nächstniedrigere Liga.

### 2.4 Phase 4: Season End Ranking

**Am Saisonende:**
1. Alle Qualifier-Ergebnisse werden gesammelt
2. **Total Score = Summe aller Qualifier-Zeiten** (niedriger = besser)
3. Ranking nach niedrigster Gesamtzeit

### 2.5 Phase 5: Liga Zuweisung (Promotion/Relegation)

| Liga  | Aufsteiger (von unten) | Absteiger (nach unten) |
|-------|------------------------|------------------------|
| F1    | Top 2 aus F2           | Bottom 2 → F2          |
| F2    | Top 2 aus F3 + 2 von F1| Bottom 2 → F3          |
| F3    | Top 2 aus F4 + 2 von F2| Bottom 2 → F4          |
| ...   | ...                    | ...                    |
| F9    | Top 2 aus F10 + 2 v.F8 | Bottom 2 → F10         |
| F10   | Top 2 aus F10 bleiben  | Bottom 2 → raus (Warteliste) |

**Optional: Playoffs**
- Position 2 und 3 in der Relegationszone fahren Playoffs
- 1 Rennen, 3 Runden, Gewinner bleibt/steigt auf

---

## 3. RACE & QUALIFYING SYSTEM

### 3.1 Lap Time Simulation

Jeder Fahrer fährt eine Rundenzeit basierend auf multiplen Faktoren.

#### Formel:

```
LapTime_ms =
    BaseTrackTime_ms
    - DriverSkillBonus_ms
    - TeamBonus_ms
    - CarPerformance_ms
    + RandomVariance_ms
    + WeatherPenalty_ms
    + TyreDegradation_ms
```

#### Detaillierte Aufschlüsselung:

**BaseTrackTime_ms:** Streckenabhängige Basiszeit (z.B. 90.000ms = 1:30.000)

**DriverSkillBonus_ms:**
```
QualifyingWeight = 0.35
SpeedWeight = 0.30
ConsistencyWeight = 0.15
MentalWeight = 0.10
WetWeight = 0.10 (nur bei Regen)

DriverBonus = (
    Driver.QualifyingPace * QualifyingWeight +
    Driver.Speed * SpeedWeight +
    Driver.Consistency * ConsistencyWeight +
    Driver.MentalStrength * MentalWeight
) / 100 * 5000ms  // Max 5s Bonus
```

**TeamBonus_ms:**
```
TeamBonus = Team.PerformanceRating / 100 * 2000ms  // Max 2s Bonus
```

**RandomVariance_ms:**
- Normalverteilt, mean=0, stddev=500ms
- Seed-basiert für Reproduzierbarkeit

**WeatherPenalty_ms:**
| Wetter  | Penalty     | Wet-Stat-Effekt |
|---------|-------------|-----------------|
| Dry     | 0ms         | —               |
| Light Rain | +500ms   | Wet*0.5 reduziert|
| Heavy Rain | +1500ms  | Wet*0.8 reduziert|
| Storm   | +3000ms     | Wet*0.9 reduziert|

**TyreDegradation_ms:**
- Pro Runde: +50ms * (1 - Driver.TyreManagement/100)
- Qualifier = Runde 1 → minimaler Effekt

### 3.2 Race Simulation (Offline)

**Rennformat:** 20–70 Runden (pro Liga skalierend).

**Rennausgabe:**
```
1. L. Moretti (ITA) — 1:32:45.234 — +0.000
2. K. Sato (JPN) — 1:32:47.891 — +2.657
3. E. Walker (UK) — 1:32:50.123 — +4.889
...
```

**Rennereignisse:**
- Überholmanöver (Overtaking-Stat)
- Boxenstopps (Tyre Management)
- Safety Car Phasen (Zufall)
- Unfälle (Aggression + Risk Taking)
- Wetterwechsel

### 3.3 Wettersystem

```
┌─────────────┐
│   WEATHER   │
│  ROLL (d20) │
├─────────────┤
│  1-10: Dry  │
│ 11-14: Clouds │
│ 15-17: Light Rain │
│ 18-19: Heavy Rain  │
│   20: Storm │
└─────────────┘
```

- Wetter wird **pro Rennen** gewürfelt
- Saisons haben Klima-Präferenz (z.B. Europa-Sommer = trockener)
- Wetter bleibt für Qualifier + Rennen gleich

---

## 4. PROCEDURAL DRIVER SYSTEM

### 4.1 Basisdaten

```json
{
  "id": "uuid",
  "firstName": "Luca",
  "lastName": "Moretti",
  "nationality": "IT",
  "age": 22,
  "season": 1,
  "retired": false
}
```

**Altersspanne:** 16–38 (Neugenerierung), maximal 45 (Karriereende)

### 4.2 Sichtbare Attribute (0–100)

| Attribut | Beschreibung | Gewicht Qualifier | Gewicht Rennen |
|----------|-------------|-------------------|----------------|
| Speed | Reine Geschwindigkeit | 0.30 | 0.25 |
| Consistency | Rundenkonstanz | 0.15 | 0.20 |
| Racecraft | Rennintelligenz | 0.05 | 0.20 |
| Overtaking | Überholfähigkeit | 0.00 | 0.15 |
| Tyre Management | Reifenschonung | 0.05 | 0.10 |
| Qualifying Pace | Qualifying-Spezialist | 0.35 | 0.00 |
| Wet Performance | Regenkönner | 0.10 | 0.10 |
| Mental Strength | Druckresistenz | 0.10 | 0.10 |

### 4.3 Versteckte Stats

```json
{
  "potential": 85,       // 0-100, maximal erreichbares Overall
  "growthRate": 0.8,     // 0.1-1.5, Wachstumsgeschwindigkeit
  "aggression": 60,      // 0-100, Unfallrisiko
  "riskTaking": 45,      // 0-100, riskante Manöver
  "pressureHandling": 70 // 0-100, Leistung unter Druck
}
```

### 4.4 Persönlichkeit

```python
PERSONALITY_TYPES = {
    "calm": {
        "desc": "Gleichmäßig, stabil, selten Fehler",
        "modifiers": {"consistency": +5, "riskTaking": -20}
    },
    "aggressive": {
        "desc": "Maximales Risiko, viele Überholmanöver, viele Unfälle",
        "modifiers": {"overtaking": +10, "aggression": +20, "riskTaking": +15}
    },
    "inconsistent": {
        "desc": "Mal Weltklasse, mal Katastrophe",
        "modifiers": {"consistency": -15, "variance_mult": 2.0}
    },
    "strategic": {
        "desc": "Denkt mehrere Züge voraus, exzellentes Tyre Management",
        "modifiers": {"tyreMgmt": +10, "racecraft": +10}
    },
    "clutch": {
        "desc": "Liefert unter Druck Höchstleistungen",
        "modifiers": {"mental": +15, "pressureHandling": +20}
    }
}
```

### 4.5 Entwicklungssystem

#### Altersphasen:

| Alter    | Phase        | Wachstumsmultiplikator | Attributveränderung |
|----------|-------------|----------------------|---------------------|
| 16–19    | Rookie       | 1.5×                  | Schneller Aufbau    |
| 20–22    | Entwicklung  | 1.2×                  | Stabiler Aufbau     |
| 23–27    | Peak         | 1.0×                  | Maximalniveau       |
| 28–30    | Spät-Peak    | 0.7×                  | Leichter Abbau      |
| 31–35    | Veteran      | 0.3×                  | Langsamer Abbau     |
| 36–45    | Decline      | 0.0×                  | Beschleunigter Abbau|

#### Entwicklungsformel (pro Rennen):

```python
def develop_driver(driver, team_quality, results_score, training_level):
    """results_score: 0-100 basierend auf Rennergebnis"""
    if driver.age >= 36:
        # Decline: Abbau unvermeidbar
        decay = (driver.age - 35) * 0.3
        for attr in ALL_ATTRIBUTES:
            driver.attributes[attr] = max(10, driver.attributes[attr] - decay * random())
        return

    growth_mult = AGE_GROWTH_MULT[driver.age_group()]
    base_growth = driver.growthRate * growth_mult * 0.1

    for attr in ALL_ATTRIBUTES:
        # Wachstum durch Training + Ergebnisse
        gain = base_growth * team_quality/100 * (1 + results_score/100)
        gain += training_level * 0.05

        # Potential-Deckel
        current = driver.attributes[attr]
        max_possible = driver.potential * (1 + (100 - driver.potential)/200)
        if current < max_possible:
            driver.attributes[attr] = min(max_possible, current + gain)

    # Decline-Phase: Abbau startet
    if driver.age >= 31:
        decay = (driver.age - 30) * 0.15
        for attr in ALL_ATTRIBUTES:
            driver.attributes[attr] -= decay
```

---

## 5. NAME GENERATION SYSTEM

### 5.1 Regionen & Gewichtung

```python
REGIONS = {
    "europe": {
        "weight": 0.40,
        "countries": ["UK", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "FI", "SE", "DK", "PL", "PT", "GR", "RU"]
    },
    "south_america": {
        "weight": 0.15,
        "countries": ["BR", "AR", "CO", "CL", "PE", "UY"]
    },
    "north_america": {
        "weight": 0.15,
        "countries": ["US", "CA", "MX"]
    },
    "asia": {
        "weight": 0.15,
        "countries": ["JP", "CN", "KR", "IN", "TH", "MY", "ID", "AE"]
    },
    "africa": {
        "weight": 0.10,
        "countries": ["ZA", "NG", "KE", "MA", "EG", "GH"]
    },
    "oceania": {
        "weight": 0.05,
        "countries": ["AU", "NZ"]
    }
}
```

### 5.2 Namensgenerator Beispiele

**Europa:** Luca Moretti (IT), Ethan Walker (UK), Finn Schröder (DE), Hugo Dubois (FR), Mateo García (ES), Lars Bergström (SE)

**Südamerika:** Carlos Mendes (BR), Santiago López (AR), Pablo Ruiz (CO), Thiago Silva (BR)

**Nordamerika:** Jackson Miller (US), Marcus Thompson (US), Liam O'Connell (CA), Diego Ramirez (MX)

**Asien:** Kenji Sato (JP), Wei Chen (CN), Min-Jun Park (KR), Arjun Patel (IN), Somchai Thong (TH)

**Afrika:** Thabo Nkosi (ZA), Kofi Mensah (GH), Ahmed Hassan (EG), Chidi Okonkwo (NG)

**Ozeanien:** Jack Thompson (AU), James Sullivan (AU), Liam Anderson (NZ)

### 5.3 Länder-Attribut-Bonus (optional)

```python
COUNTRY_BONUSES = {
    "IT": {"speed": 5},          # Italien: Geschwindigkeit
    "BR": {"overtaking": 5},     # Brasilien: Überholen
    "UK": {"consistency": 5},    # UK: Konstanz
    "DE": {"tyre_mgmt": 5},      # Deutschland: Reifenmanagement
    "JP": {"qualifying": 5},     # Japan: Qualifying
    "FI": {"wet": 5},            # Finnland: Regen
    "FR": {"racecraft": 5},      # Frankreich: Rennintelligenz
    "ES": {"mental": 5},         # Spanien: Mentale Stärke
}
```

---

## 6. TEAM SYSTEM

### 6.1 Team-Struktur

```python
@dataclass
class Team:
    id: str
    name: str
    owner_id: int              # Discord User ID
    league: int                # 1-10 (F1-F10)
    
    # Performance
    budget: float              # Aktuelles Budget
    performance_rating: int    # 0-100
    infrastructure_level: int  # 0-100
    
    # Personal
    main_driver_1: Driver | None
    main_driver_2: Driver | None
    reserve_driver: Driver | None
    
    # Finanzen
    sponsor_income: float      # Pro Saison
    salary_costs: float        # Pro Saison
    prize_money: float         # Bisher in Saison
    
    # Stats
    wins: int
    podiums: int
    season_points: int
    total_qualifier_time: int  # Summe in ms (über alle Qualifier)
    
    # Premium
    is_premium: bool
    extra_slots: int           # Zusätzliche Team-Slots (Premium)
```

### 6.2 Team-Fähigkeiten

```python
TEAM_UPGRADES = {
    "aerodynamics": {
        "max_level": 10,
        "cost_per_level": [500000, 800000, 1200000, ...],
        "effect": "performance_rating +2 pro Level"
    },
    "engine": {
        "max_level": 10,
        "effect": "performance_rating +3 pro Level"
    },
    "simulator": {
        "max_level": 5,
        "effect": "driver_development +10% pro Level"
    },
    "pit_crew": {
        "max_level": 5,
        "effect": "race_strategy_bonus",
        "cost_per_level": [200000, 350000, ...]
    },
    "scouting": {
        "max_level": 3,
        "effect": "bessere Academy-Fahrer",
        "cost_per_level": [100000, 250000, 500000]
    }
}
```

### 6.3 Team-Kosten (pro Saison)

| Item | Kosten | Beschreibung |
|------|--------|-------------|
| Fahrer-Gehälter | Variabel | Abhängig von Fahrer-Stärke |
| Infrastruktur | 200k–2M | Level-abhängig |
| Entwicklung | 100k–5M | Upgrades |
| Training | 50k–500k | Team-Training |
| Academy | 100k–1M | Nachwuchsförderung |

---

## 7. SPONSOR SYSTEM

### 7.1 Sponsor-Generierung

```python
@dataclass
class Sponsor:
    id: str
    name: str
    type: SponsorType  # LOCAL, REGIONAL, GLOBAL, MEGA
    budget: float      # Gesamtbudget pro Saison
    requirements: dict  # {"min_performance": 50, "min_league": 3}
    bonus_conditions: dict  # {"wins": 500000, "podiums": 200000}
    driver_nationality_bonus: bool  # Bevorzugt Fahrer aus bestimmten Ländern
```

### 7.2 Sponsor-Typen

| Typ | Budget | Voraussetzung | Beispiel |
|-----|--------|--------------|----------|
| Local | 0.5M–2M | Keine | "Münchner Bier GmbH" |
| Regional | 2M–5M | Liga F5+ | "EuroWheels Tyres" |
| Global | 5M–10M | Liga F3+ | "GlobalOil Corp" |
| Mega | 10M–20M | Liga F1-F2 | "Titans Energy Drink" |
| Title | 15M–30M | Liga F1, Top 3 | "Apex Racing" (Team wird umbenannt) |

### 7.3 Dynamische Sponsoren-Faktoren

- **Fahrer-Nationalität:** Lokale Sponsoren zahlen Bonus, wenn Fahrer aus derselben Region
- **Team Performance:** Bessere Ergebnisse → bessere Sponsoren
- **Liga:** Höhere Liga → höhere Budgets
- **Vertragslaufzeit:** 1–3 Seasons, Neuverhandlung nach Ablauf

---

## 8. ACADEMY SYSTEM

### 8.1 Jährlicher Academy-Drop

**Zeitpunkt:** Post-Season (vor Pre-Season der nächsten Saison)

**Anzahl:** 5–15 neue Fahrer (abhängig von globaler Fahreranzahl)

**Qualität:**
```python
def generate_academy_driver(team_scouting_level):
    base_potential = randint(40, 95)  # Akademie-Fahrer haben niedrigere Baseline
    scouting_bonus = team_scouting_level * 3
    potential = min(99, base_potential + scouting_bonus)
    
    # Attribute werden basierend auf Potential generiert
    attrs = {}
    for attr in ALL_ATTRIBUTES:
        base = randint(30, 60)  # Academy-Fahrer starten niedrig
        attrs[attr] = min(99, base + (potential - 40) * 0.5)
    
    return Driver(
        age=randint(16, 19),
        potential=potential,
        growthRate=uniform(0.6, 1.4),
        attributes=attrs,
        personality=random_choice(PERSONALITY_TYPES)
    )
```

### 8.2 Scout-System

| Scout-Level | Effekt | Kosten/Saison |
|-------------|--------|--------------|
| 1 (Basic) | +1 Fahrer, +0 Bonus | 100k |
| 2 (Regional) | +2 Fahrer, +5 Potential | 250k |
| 3 (International) | +3 Fahrer, +10 Potential | 500k |

**Region-Scouting:** Scout kann auf eine Region spezialisiert werden → höhere Attribute für Fahrer aus dieser Region.

---

## 9. SEASON STRUCTURE

### 9.1 Saison-Ablauf

```
WOCHE 1-2:   Pre-Season
             • Kaderplanung (Transfers, Verträge)
             • Sponsor-Suche
             • Team-Upgrades kaufen
             • Training

WOCHE 3-14:  Season (12 Rennen)
             • Rennen (Mi/So oder flexibel)
             • Qualifier nach jedem Rennen (24h Fenster)
             • Fahrerentwicklung

WOCHE 15-16: Post-Season
             • Ranking-Berechnung
             • Promotion/Relegation
             • Academy-Drop
             • Budget-Update
             • Neue Saison beginnt
```

### 9.2 Pre-Season Phase

1. **Team-Kader festlegen** — Fahrer verpflichten/entlassen
2. **Sponsor-Verhandlungen** — Neue Sponsoren suchen, alte verlängern
3. **Upgrades kaufen** — Budget in Team-Upgrades investieren
4. **Training** — Fahrer erhalten Baseline-Training

### 9.3 In-Season Phase

**Pro Woche (12–24 Runden):**
1. **Offline-Rennen** — Simulation mit aktuellen Fahrern + Team
2. **Online-Qualifier** — 24h-Fenster zur Teilnahme
3. **Ergebnisse** — Veröffentlichung der Qualifier-Rankings

### 9.4 Post-Season Phase

1. **Qualifier-Ranking** — Alle Zeiten summiert
2. **Promotion/Relegation** — Top 2 / Bottom 2
3. **Academy-Drop** — Neue Fahrer generiert
4. **Fahrer-Karriereende** — Fahrer >45 Jahre alt → Retirement
5. **Budget-Update** — Preisgelder + Sponsoren - Kosten
6. **Reset** — Neue Saison startet

---

## 10. MONETARISIERUNG

### 10.1 Free Tier

| Feature | Free | Premium |
|---------|------|---------|
| Teams | 1 | 3–5 |
| Liga-Teilnahme | Ja | Ja |
| Qualifier | Max 20/Saison | Unbegrenzt |
| Trainings-Slots | 1/Woche | 3/Woche |
| Analytics | Basis (Platzierung) | Detailliert (Heatmaps, Trends) |
| Simulation Speed | Normal | 2× Schnell |
| History | Letzte Saison | Alle Seasons |
| Academy Scouts | Level 1 | Level 1–3 |

### 10.2 Premium (5–10€/Monat)

- 3–5 Team-Slots
- Unbegrenzte Qualifier-Teilnahme
- Detaillierte Simulations-Reports (Rundenanalysen, Fahrer-Heatmaps)
- 2× Simulationsgeschwindigkeit
- Vollständige Season-History
- Export-Funktion (CSV/JSON)

### 10.3 Optionale Käufe (Kein Pay-to-Win)

| Item | Preis | Effekt |
|------|-------|--------|
| Extra Team Slot | 3€ (einmalig) | +1 Team (max +2) |
| Custom Branding | 5€ (einmalig) | Eigenes Team-Logo/Banner |
| Season Pass | 8€/Season | Exklusive Events + Belohnungen |
| Private Liga | 15€/Monat | Eigene Liga mit Freunden |
| Driver Slot | 2€ (einmalig) | +1 Fahrer-Slot (max +1) |

---

## 11. DISCORD INTEGRATION

### 11.1 Commands (Minimalset)

```
/team           — Team-Übersicht (Name, Liga, Budget, Fahrer)
/team lineup    — Aufstellung setzen
/team upgrade   — Upgrades kaufen

/race           — Aktuelles Rennen simulieren (Offline)
/race result    — Letztes Rennergebnis

/drivers        — Fahrer-Liste
/driver <id>    — Fahrer-Details (Stats, Entwicklung)

/market         — Transfermarkt
/market buy     — Fahrer kaufen
/market sell    — Fahrer verkaufen

/season         — Saison-Status
/season standings — Aktuelle Tabelle
/season schedule — Rennkalender

/qualifier      — Qualifier-Übersicht
/qualifier run  — Qualifier fahren (3 Fahrer)
/qualifier result — Letztes Qualifier-Ergebnis
/qualifier ranking — Liga-Ranking

/train          — Training absolvieren
/train status   — Trainings-Status

/sponsor        — Sponsor-Übersicht
/sponsor negotiate — Sponsor-Verhandlung

/academy        — Academy-Übersicht
/academy scout  — Scout einsetzen

/league         — Liga-Infos (alle 10 Ligen)
/league ranking — Globales Ranking

/premium        — Premium-Infos
/premium status — Premium-Status
```

### 11.2 Embed-Design (Beispiel)

```
┌──────────────────────────────────────┐
│ 🏁 TEAM APEX RACING                   │
│ Liga: F3 • Budget: €4,250,000         │
├──────────────────────────────────────┤
│ 🏎️ Fahrer:                             │
│ ┌──────────────────────────────────┐  │
│ │ #1 Luca Moretti (IT) ⭐⭐⭐½       │  │
│ │ Alter: 24 • Speed: 87 • Con: 72  │  │
│ │ Form: 🔥 Letztes Rennen: P2     │  │
│ ├──────────────────────────────────┤  │
│ │ #2 Kenji Sato (JP) ⭐⭐⭐          │  │
│ │ Alter: 22 • Speed: 79 • Con: 81  │  │
│ │ Form: ✅ Letztes Rennen: P5     │  │
│ ├──────────────────────────────────┤  │
│ │ RES: Ethan Walker (UK) ⭐⭐       │  │
│ │ Alter: 19 • Talent: Hoch        │  │
│ └──────────────────────────────────┘  │
├──────────────────────────────────────┤
│ 🏆 Saison: 3 Siege • 5 Podien • P4  │
│ 📊 Qualifier: 3. Gesamtzeit: +2.3s  │
│ 💰 Sponsoren: EuroWheels (€3.2M)    │
└──────────────────────────────────────┘
```

### 11.3 Interaktive Komponenten

- **Buttons:** `[Rennen simulieren]` `[Qualifier fahren]` `[Training]`
- **Select Menus:** Fahrer-Auswahl für Aufstellung
- **Modals:** Team-Name ändern, Setup-Konfiguration
- **Persistente Views:** Team-Übersicht, die automatisch aktualisiert

---

## 12. TECHNICAL ARCHITECTURE

### 12.1 High-Level Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    DISCORD BOT LAYER                    │
│  discord.py / nextcord                                   │
│  • Command Handler (Slash + Prefix)                      │
│  • View Manager (Buttons, Selects, Modals)               │
│  • Embed Builder                                         │
│  • Permission Checker                                    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    GAME LAYER                           │
│  • Simulation Engine (deterministisch)                  │
│  • State Manager (World State)                          │
│  • Event Scheduler                                      │
│  • Ranking System                                       │
│  • Driver Development Engine                            │
│  • Economy Manager                                      │
│  • Sponsor Engine                                       │
│  • Academy Generator                                    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    DATA LAYER                           │
│  • Database (SQLite/PostgreSQL)                          │
│  • Cache (Redis optional)                                │
│  • Config Manager                                        │
│  • Seed Store (für deterministische Sims)               │
└─────────────────────────────────────────────────────────┘
```

### 12.2 Technologie-Stack

| Komponente | Technologie | Begründung |
|-----------|-------------|-----------|
| Bot Framework | discord.py (2.4+) | Bewährt, async-native, Slash-Commands |
| Database | PostgreSQL | ACID, JSON-Felder, komplexe Queries für Ranking |
| ORM | SQLAlchemy 2.0 | Async, Type-Hints, Migrationen via Alembic |
| Cache | Redis (optional) | Leaderboard-Caching, Rate-Limiting |
| Simulation | Pure Python (NumPy optional) | Deterministisch via random.seed() |
| Task Queue | APScheduler | Cron-Jobs für Season-Events |
| Hosting | VPS (4GB RAM+) | Für 100+ parallele Universen |

### 12.3 Deterministische Simulation

```python
import random
import hashlib

class SimSeed:
    """Erzeugt deterministische Seeds für reproduzierbare Simulationen."""
    
    @staticmethod
    def for_race(season: int, race_number: int, universe_id: str) -> int:
        key = f"{universe_id}:S{season}:R{race_number}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    
    @staticmethod
    def for_qualifier(season: int, race_number: int, league: int, team_id: str) -> int:
        key = f"QUAL:{season}:{race_number}:L{league}:{team_id}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
    
    @staticmethod
    def for_driver_gen(season: int, region: str) -> int:
        key = f"DRIVERGEN:S{season}:{region}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
```

---

## 13. DATABASE SCHEMA

### 13.1 Kern-Tabellen

```sql
-- Spieler / Universen
CREATE TABLE players (
    id BIGINT PRIMARY KEY,  -- Discord User ID
    username TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    is_premium BOOLEAN DEFAULT FALSE,
    premium_since TIMESTAMP,
    total_seasons INTEGER DEFAULT 0
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id BIGINT REFERENCES players(id),
    name TEXT NOT NULL,
    league INTEGER NOT NULL CHECK (league BETWEEN 1 AND 10),
    budget DECIMAL(14,2) DEFAULT 1000000.00,
    performance_rating INTEGER DEFAULT 50,
    infrastructure_level INTEGER DEFAULT 1,
    sponsor_income DECIMAL(12,2) DEFAULT 0,
    salary_costs DECIMAL(12,2) DEFAULT 0,
    prize_money DECIMAL(12,2) DEFAULT 0,
    wins INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    season_points INTEGER DEFAULT 0,
    total_qualifier_time BIGINT DEFAULT 0,  -- in ms
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    active_season INTEGER DEFAULT 1
);

-- Fahrer
CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    nationality TEXT NOT NULL,
    age INTEGER NOT NULL,
    
    -- Sichtbare Stats (0-100)
    speed INTEGER DEFAULT 50,
    consistency INTEGER DEFAULT 50,
    racecraft INTEGER DEFAULT 50,
    overtaking INTEGER DEFAULT 50,
    tyre_management INTEGER DEFAULT 50,
    qualifying_pace INTEGER DEFAULT 50,
    wet_performance INTEGER DEFAULT 50,
    mental_strength INTEGER DEFAULT 50,
    
    -- Versteckte Stats
    potential INTEGER DEFAULT 50,
    growth_rate REAL DEFAULT 1.0,
    aggression INTEGER DEFAULT 50,
    risk_taking INTEGER DEFAULT 50,
    pressure_handling INTEGER DEFAULT 50,
    
    -- Status
    personality TEXT DEFAULT 'calm',
    slot INTEGER CHECK (slot IN (1, 2, 3)),  -- 1=Haupt, 2=Haupt, 3=Reserve
    morale INTEGER DEFAULT 50,
    is_academy BOOLEAN DEFAULT FALSE,
    is_retired BOOLEAN DEFAULT FALSE,
    retirement_season INTEGER,
    
    -- Stats
    wins INTEGER DEFAULT 0,
    podiums INTEGER DEFAULT 0,
    races_driven INTEGER DEFAULT 0,
    season VARCHAR(20)
);

-- Rennen (Offline)
CREATE TABLE races (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    season INTEGER NOT NULL,
    race_number INTEGER NOT NULL,
    track_name TEXT,
    weather TEXT DEFAULT 'dry',
    -- Ergebnisse
    driver_1_position INTEGER,
    driver_2_position INTEGER,
    driver_1_time BIGINT,  -- in ms
    driver_2_time BIGINT,
    race_events JSONB,      -- Ereignisse während des Rennens
    simulated_at TIMESTAMP DEFAULT NOW()
);

-- Qualifier (Online)
CREATE TABLE qualifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    league INTEGER NOT NULL CHECK (league BETWEEN 1 AND 10),
    season INTEGER NOT NULL,
    race_number INTEGER NOT NULL,
    
    -- Fahrer-Zeiten
    driver_1_time BIGINT,    -- in ms
    driver_2_time BIGINT,
    driver_3_time BIGINT,
    average_time BIGINT,     -- (d1 + d2 + d3) / 3
    
    was_auto BOOLEAN DEFAULT FALSE,  -- TRUE wenn Standardzeit verwendet
    submitted_at TIMESTAMP DEFAULT NOW()
);

-- Saison-Ranking
CREATE TABLE season_rankings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league INTEGER NOT NULL,
    season INTEGER NOT NULL,
    team_id UUID REFERENCES teams(id),
    total_time BIGINT NOT NULL,     -- Summe aller Qualifier-Zeiten
    average_time BIGINT NOT NULL,   -- Durchschnittszeit
    rank INTEGER NOT NULL,
    promotion_eligible BOOLEAN DEFAULT FALSE,
    relegation_eligible BOOLEAN DEFAULT FALSE,
    new_league INTEGER,              -- Ziel-Liga nach Promotion/Relegation
    UNIQUE(league, season, team_id)
);

-- Sponsoren
CREATE TABLE sponsors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('local', 'regional', 'global', 'mega', 'title')),
    budget DECIMAL(12,2) NOT NULL,
    contract_seasons INTEGER DEFAULT 1,
    seasons_remaining INTEGER DEFAULT 1,
    requirements JSONB,
    bonus_conditions JSONB,
    signed_at TIMESTAMP DEFAULT NOW()
);

-- Team-Upgrades
CREATE TABLE team_upgrades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    upgrade_type TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    purchased_at TIMESTAMP DEFAULT NOW()
);

-- Academy-Scouts
CREATE TABLE academy_scouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    level INTEGER NOT NULL DEFAULT 1,
    region TEXT,
    hired_at TIMESTAMP DEFAULT NOW()
);

-- Transfers / Market History
CREATE TABLE transfer_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID REFERENCES drivers(id),
    from_team_id UUID REFERENCES teams(id),
    to_team_id UUID REFERENCES teams(id),
    fee DECIMAL(12,2),
    season INTEGER NOT NULL,
    transferred_at TIMESTAMP DEFAULT NOW()
);

-- Events (dynamische Welt-Ereignisse)
CREATE TABLE world_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    event_type TEXT NOT NULL,
    description TEXT,
    effects JSONB,
    season INTEGER NOT NULL,
    race_number INTEGER,
    happened_at TIMESTAMP DEFAULT NOW()
);
```

---

## 14. SIMULATION ENGINE SPEC

### 14.1 Engine-Architektur

```python
class SimulationEngine:
    """
    Deterministische Simulations-Engine.
    Alle Ergebnisse sind über Seeds reproduzierbar.
    """
    
    def __init__(self, universe_id: str):
        self.universe_id = universe_id
        self.seed_generator = SimSeed()
    
    def simulate_race(self, team: Team, season: int, race_number: int, 
                      track: Track, weather: str) -> RaceResult:
        """Simuliert ein komplettes Rennen."""
        seed = self.seed_generator.for_race(season, race_number, self.universe_id)
        rng = random.Random(seed)
        
        # Fahrer analysieren
        d1_result = self._simulate_driver_race(
            team.main_driver_1, team, track, weather, rng
        )
        d2_result = self._simulate_driver_race(
            team.main_driver_2, team, track, weather, rng
        )
        
        # Rennereignisse generieren
        events = self._generate_race_events(d1_result, d2_result, team, rng)
        
        # Team-Punktestand aktualisieren
        points = self._calculate_points(d1_result, d2_result)
        
        return RaceResult(
            driver_1=d1_result,
            driver_2=d2_result,
            team_points=points,
            events=events,
            weather=weather,
            track=track
        )
    
    def simulate_qualifier_lap(self, driver: Driver, team: Team, 
                                league: int, season: int, 
                                race_number: int, weather: str) -> int:
        """Simuliert EINE Qualifier-Runde in ms."""
        seed = self.seed_generator.for_qualifier(
            season, race_number, league, team.id
        )
        rng = random.Random(seed)
        
        # Basiseit (90s = 90.000ms, je nach Liga anders)
        base_time = self._get_base_time(league)
        
        # Fahrer-Bonus (0–5000ms)
        driver_bonus = self._calculate_qualifying_bonus(driver, weather)
        
        # Team-Bonus (0–2000ms)
        team_bonus = self._calculate_team_bonus(team)
        
        # Zufallsvarianz (normalverteilt, mean=0, stddev=500ms)
        variance = int(rng.gauss(0, 500))
        
        # Wetter-Effekt
        weather_penalty = WEATHER_PENALTIES.get(weather, 0)
        
        if weather != "dry":
            # Wet-Performance reduziert Wetter-Penalty
            wet_factor = 1 - (driver.wet_performance / 100 * 0.5)
            weather_penalty = int(weather_penalty * wet_factor)
        
        lap_time = base_time - driver_bonus - team_bonus + variance + weather_penalty
        
        return max(60000, lap_time)  # Minimum 60s
    
    def _calculate_qualifying_bonus(self, driver: Driver, weather: str) -> int:
        """Berechnet den Zeitbonus durch Fahrer-Stats."""
        weights = {
            "qualifying_pace": 0.35,
            "speed": 0.30,
            "consistency": 0.15,
            "mental_strength": 0.10,
            "wet_performance": 0.10 if weather != "dry" else 0.05
        }
        
        # Anpassen falls trocken
        if weather == "dry":
            weights["speed"] = 0.35
            weights["wet_performance"] = 0.00
            weights["mental_strength"] = 0.10
        
        weighted_score = sum(
            getattr(driver, attr) * weight 
            for attr, weight in weights.items()
        )
        
        # Max 5000ms Bonus (bei weighted_score = 100)
        return int(weighted_score * 50)
    
    def _calculate_team_bonus(self, team: Team) -> int:
        """Berechnet den Zeitbonus durch Team-Performance."""
        return int(team.performance_rating * 20)  # Max 2000ms
```

### 14.2 Qualifier-Ranking Berechnung

```python
class RankingCalculator:
    """Berechnet Season-End-Rankings und Promotion/Relegation."""
    
    @staticmethod
    def calculate_season_ranking(qualifiers: list[QualifierResult]) -> list[TeamRank]:
        """
        Summiert alle Qualifier-Zeiten pro Team.
        Niedrigste Gesamtzeit = Bestes Ranking.
        """
        team_times: dict[str, list[int]] = {}
        
        for q in qualifiers:
            if q.team_id not in team_times:
                team_times[q.team_id] = []
            team_times[q.team_id].append(q.average_time)
        
        rankings = []
        for team_id, times in team_times.items():
            total_time = sum(times)
            avg_time = total_time // len(times)
            rankings.append(TeamRank(
                team_id=team_id,
                total_time=total_time,
                average_time=avg_time,
                qualifiers_run=len(times)
            ))
        
        # Sortieren: Niedrigste Zeit zuerst
        rankings.sort(key=lambda r: r.total_time)
        
        # Rang zuweisen
        for i, rank in enumerate(rankings, 1):
            rank.rank = i
        
        return rankings
    
    @staticmethod
    def calculate_promotion_relegation(
        league: int, 
        rankings: list[TeamRank]
    ) -> PromotionResult:
        """
        Bestimmt Auf- und Absteiger.
        Top 2 → Promotion
        Bottom 2 → Relegation
        """
        total_teams = len(rankings)
        
        if total_teams < 4:
            return PromotionResult(promotions=[], relegations=[])
        
        promotions = rankings[:2]    # Top 2
        relegations = rankings[-2:]  # Bottom 2
        
        return PromotionResult(
            promotions=[r.team_id for r in promotions],
            relegations=[r.team_id for r in relegations],
            promotion_league=league - 1 if league > 1 else None,
            relegation_league=league + 1 if league < 10 else None
        )
```

---

## 15. STATE MACHINE & EVENT SYSTEM

### 15.1 Global Season State Machine

```
                 ┌─────────────────┐
                 │   PRE_SEASON    │
                 │ (2 Wochen)      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
          ┌──────│   SEASON_ACTIVE  │◄────┐
          │      │ (12-24 Rennen)  │     │
          │      └────────┬────────┘     │
          │               │              │
          │         ┌─────▼──────┐       │
          │         │  RACE_DAY  │       │
          │         │ (Rennen    │       │
          │         │  + Quali)  │       │
          │         └─────┬──────┘       │
          │               │              │
          │         ┌─────▼──────┐       │
          │         │ QUALIFIER  │       │
          │         │ (24h Fenster)│     │
          │         └─────┬──────┘       │
          │               │              │
          │        Noch Rennen?          │
          │         ┌────┤              │
          │        Ja  Nein              │
          │         │    │              │
          └─────────┘    │              │
                         ▼              │
                ┌─────────────────┐     │
                │  POST_SEASON    │     │
                │ (Ranking,       │     │
                │  Prom/Rel,      │     │
                │  Academy)       │     │
                └────────┬────────┘     │
                         │              │
                         ▼              │
                ┌─────────────────┐     │
                │   NEW_SEASON    │─────┘
                │ (Pre-Season)    │
                └─────────────────┘
```

### 15.2 Event Scheduler (Cron-basiert)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class SeasonScheduler:
    """Plant alle Season-Events per Cron-Job."""
    
    def __init__(self, bot, db):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.db = db
    
    def start(self):
        # Wöchentlicher Renn-Tick (z.B. jeden Mittwoch + Samstag)
        self.scheduler.add_job(
            self.race_tick,
            CronTrigger(day_of_week="wed,sat", hour=12, minute=0),
            id="race_tick"
        )
        
        # Qualifier-Deadline (24h nach Rennen)
        self.scheduler.add_job(
            self.qualifier_deadline,
            CronTrigger(day_of_week="thu,sun", hour=12, minute=0),
            id="qualifier_deadline"
        )
        
        # Post-Season Start
        self.scheduler.add_job(
            self.start_post_season,
            CronTrigger(day_of_week="mon", hour=12, minute=0),
            id="post_season"
        )
        
        self.scheduler.start()
    
    async def race_tick(self):
        """Simuliert Rennen für ALLE aktiven Teams."""
        teams = await self.db.get_all_active_teams()
        engine = SimulationEngine(universe_id="global")
        
        for team in teams:
            result = engine.simulate_race(
                team, 
                season=team.active_season,
                race_number=team.current_race + 1,
                track=get_random_track(),
                weather=roll_weather()
            )
            await self.db.save_race_result(team.id, result)
            await self._notify_team(team.owner_id, result)
    
    async def qualifier_deadline(self):
        """Schließt Qualifier-Fenster, berechnet Average."""
        # Teams, die NICHT teilgenommen haben, erhalten Standardzeit
        missing_teams = await self.db.get_teams_without_qualifier()
        for team in missing_teams:
            penalty = LEAGUE_PENALTIES[team.league]
            median = await self.db.get_league_median(team.league)
            standard_time = median + penalty
            
            await self.db.save_qualifier(
                team_id=team.id,
                season=team.active_season,
                race_number=team.current_race,
                driver_1_time=standard_time,
                driver_2_time=standard_time,
                driver_3_time=standard_time,
                average_time=standard_time,
                was_auto=True
            )
    
    async def start_post_season(self):
        """Startet Post-Season: Ranking, Promotion, Academy."""
        for league in range(1, 11):
            qualifiers = await self.db.get_season_qualifiers(league)
            rankings = RankingCalculator.calculate_season_ranking(qualifiers)
            
            promotion = RankingCalculator.calculate_promotion_relegation(
                league, rankings
            )
            
            await self.db.save_season_rankings(league, rankings)
            await self.db.apply_promotion_relegation(promotion)
        
        # Academy-Drop
        await self._generate_academy_drivers()
```

### 15.3 Event System (Dynamische Welt-Events)

```python
class WorldEvent:
    """Ein dynamisches Ereignis, das die Welt beeinflusst."""
    
    EVENTS = {
        "star_development": {
            "chance": 0.05,
            "desc": "{driver} hat diese Saison einen Sprung gemacht! +10 auf alle Stats",
            "effect": lambda d: {attr: min(99, d[attr] + 10) for attr in ALL_ATTRIBUTES}
        },
        "career_ending_injury": {
            "chance": 0.01,
            "desc": "{driver} hat eine schwere Verletzung — Karriere beendet.",
            "effect": lambda d: {"is_retired": True}
        },
        "sponsor_bonanza": {
            "chance": 0.03,
            "desc": "Ein großer Sponsor ist auf {driver} aufmerksam geworden!",
            "effect": lambda d: {"sponsor_budget_mult": 1.5}
        },
        "transfer_drama": {
            "chance": 0.04,
            "desc": "Gerüchte: {driver} könnte das Team verlassen.",
            "effect": lambda d: {"morale": d.get("morale", 50) - 15}
        },
        "breakthrough": {
            "chance": 0.03,
            "desc": "{driver} hat einen technischen Durchbruch erzielt!",
            "effect": lambda d: {"speed": min(99, d.get("speed", 50) + 15)}
        },
        "scandal": {
            "chance": 0.02,
            "desc": "Skandal um {driver}! Team-Image leidet.",
            "effect": lambda d: {
                "morale": d.get("morale", 50) - 20,
                "team_performance_drop": -5
            }
        },
        "mentor_effect": {
            "chance": 0.03,
            "desc": "{driver} trainiert mit einer Legende — Erfahrungsschub!",
            "effect": lambda d: {
                attr: min(99, d.get(attr, 50) + 3) 
                for attr in ["racecraft", "mental_strength", "consistency"]
            }
        }
    }
    
    @staticmethod
    def roll_events(driver, team, rng):
        events = []
        for event_name, event_data in WorldEvent.EVENTS.items():
            if rng.random() < event_data["chance"]:
                effect = event_data["effect"]({
                    **driver.__dict__,
                    "team": team.name
                })
                event = WorldEventInstance(
                    event_type=event_name,
                    description=event_data["desc"].format(
                        driver=f"{driver.first_name} {driver.last_name}",
                        team=team.name
                    ),
                    effects=effect
                )
                events.append(event)
        return events
```

---

## 16. RANKING & ELO INTEGRATION

### 16.1 Globales Fahrer-Ranking

```python
class GlobalRanking:
    """
    Berechnet ein globales Fahrer-Ranking über alle Ligen hinweg.
    
    Formel:
    Score = Driver.Overall * 0.4 
          + League_Factor * 0.3 
          + Season_Results * 0.2 
          + Team_Performance * 0.1
    
    League_Factor: F1=1.0, F2=0.9, ..., F10=0.1
    """
    
    @staticmethod
    def calculate_driver_rating(driver, league, season_stats):
        league_factor = (11 - league) / 10
        overall = sum(driver.attributes.values()) / len(driver.attributes)
        
        score = (
            overall * 0.4 +
            league_factor * 100 * 0.3 +
            season_stats * 0.2 +
            driver.team.performance_rating * 0.1
        )
        
        # Alter als Multiplikator (Peak = 25)
        age_factor = 1.0 - abs(driver.age - 25) * 0.01
        score *= max(0.85, age_factor)
        
        return int(score)
```

### 16.2 Elo-Integration (Optional)

```python
class QualifierElo:
    """
    Elo-System für Qualifier-Duelle.
    
    Jeder Qualifier ist ein indirektes Duell zwischen allen 10 Teams.
    - Sieger (beste Zeit) erhält Elo-Punkte
    - Verlierer verliert Elo-Punkte
    - Elo-Differenz beeinflusst Punkteverteilung
    """
    
    K_FACTOR = 32
    INITIAL_ELO = 1500
    
    @staticmethod
    def expected_score(elo_a: int, elo_b: int) -> float:
        return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))
    
    @staticmethod
    def update_elo(rankings: list[TeamRank], team_elos: dict[str, int]):
        """
        ratings: Liste von (team_id, elo) sortiert nach Qualifier-Zeit (beste zuerst)
        """
        teams = [(r.team_id, team_elos[r.team_id]) for r in rankings]
        
        new_elos = {}
        for i, (team_a, elo_a) in enumerate(teams):
            delta = 0
            actual_score_a = 1.0  # Gewinner gegen alle Schlechteren
            
            for j, (team_b, elo_b) in enumerate(teams):
                if i == j:
                    continue
                
                expected = QualifierElo.expected_score(elo_a, elo_b)
                
                if i < j:  # A ist besser (niedrigere Zeit)
                    actual = 1.0
                elif i > j:  # A ist schlechter (höhere Zeit)
                    actual = 0.0
                
                delta += QualifierElo.K_FACTOR * (actual - expected)
            
            new_elos[team_a] = int(elo_a + delta / (len(teams) - 1))
        
        return new_elos
```

---

## ANHANG: Implementierungs-Roadmap

### Phase 1 — Core (Woche 1-2)
- [ ] Datenbank-Schema (SQLite/PostgreSQL)
- [ ] Name-Generator (prozedural)
- [ ] Driver-Generator (Attribute + Persönlichkeit)
- [ ] Team-Modell

### Phase 2 — Simulation (Woche 3-4)
- [ ] Lap Time Simulation Engine
- [ ] Race Simulation (komplettes Rennen)
- [ ] Qualifier System
- [ ] Wetter-System

### Phase 3 — Wirtschaft (Woche 5-6)
- [ ] Sponsor-Generator
- [ ] Budget-System
- [ ] Transfermarkt
- [ ] Team-Upgrades

### Phase 4 — Online (Woche 7-8)
- [ ] Discord Commands (Slash)
- [ ] Embed Builder
- [ ] Season Scheduler (Cron)
- [ ] Qualifier-Deadlines

### Phase 5 — Liga-System (Woche 9-10)
- [ ] Ranking Calculator
- [ ] Promotion/Relegation
- [ ] Academy-System
- [ ] Event-System

### Phase 6 — Premium (Woche 11-12)
- [ ] Premium-Tier (Stripe/Patron)
- [ ] Analytics
- [ ] Private Ligen
- [ ] Custom Branding

---

*Game Design Document v1.0 — Discord Motorsport Universe*
