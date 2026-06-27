"""
Embed builders for all Discord bot commands.
Creates rich embeds for team info, race results, rankings, etc.
"""
from __future__ import annotations
from typing import Optional
from discord import Embed, Colour
from motorsport.models import (
    Team, Driver, RaceResult, QualifierResult, TeamRank,
    League, Weather, WorldEvent, ALL_ATTRIBUTES
)
from bot.config import BotConfig

cfg = BotConfig()
C = cfg.colors
E = cfg.emojis


def _league_icon(league: int) -> str:
    if league <= 2:
        return "🏆"
    elif league <= 5:
        return "🏅"
    elif league <= 8:
        return "🎯"
    return "🌱"


def _weather_icon(weather: Weather) -> str:
    icons = {
        Weather.DRY: "☀️",
        Weather.CLOUDS: "☁️",
        Weather.LIGHT_RAIN: "🌦️",
        Weather.HEAVY_RAIN: "🌧️",
        Weather.STORM: "⛈️",
    }
    return icons.get(weather, "☀️")


def _attribute_bar(value: int, max_val: int = 99, width: int = 10) -> str:
    filled = int(value / max_val * width)
    return "█" * filled + "░" * (width - filled)


def _driver_rating_stars(overall: float) -> str:
    stars = max(1, min(5, round(overall / 20)))
    return "⭐" * stars + "☆" * (5 - stars)


# ─── Team Embed ────────────────────────────────────────────────────────────

def team_embed(team: Team) -> Embed:
    league = League(f"F{team.league}")
    embed = Embed(
        title=f"{E['f1']} {team.name}",
        colour=C["primary"],
        description=f"Liga: F{team.league} {_league_icon(team.league)} "
                    f"• Budget: ${float(team.budget):,.0f}",
    )

    # Drivers
    drivers_text = ""
    for i, d in enumerate([team.main_driver_1, team.main_driver_2], 1):
        if d:
            drivers_text += (
                f"**#{i}** {d.full_name} ({d.nationality})\n"
                f"Alter: {d.age} • OVR: {d.attributes.overall():.1f} "
                f"{_driver_rating_stars(d.attributes.overall())}\n"
                f"Per: {d.personality.value} • Form: {'🔥' if d.morale > 70 else '✅' if d.morale > 40 else '⚠️'}\n\n"
            )
    embed.add_field(name=f"{E['driver']} Fahrer", value=drivers_text or "Keine Fahrer", inline=False)

    # Reserve
    if team.reserve_driver:
        r = team.reserve_driver
        embed.add_field(
            name="Reserve",
            value=f"{r.full_name} ({r.nationality}) • OVR: {r.attributes.overall():.1f}",
            inline=False
        )

    # Stats
    embed.add_field(name="Team Perf", value=f"{team.performance_rating}/100", inline=True)
    embed.add_field(name="Infrastruktur", value=f"Lv. {team.infrastructure_level}", inline=True)
    embed.add_field(name="Saison Pts", value=str(team.season_points), inline=True)
    embed.add_field(name="Siege", value=str(team.wins), inline=True)
    embed.add_field(name="Podien", value=str(team.podiums), inline=True)

    # Qualifier
    if team.total_qualifier_time_ms > 0:
        avg = team.total_qualifier_time_ms / max(1, team.qualifier_count)
        embed.add_field(name=f"{E['qualifier']} ⌀ Qualifier", value=f"{avg/1000:.3f}s", inline=True)

    embed.set_footer(text=f"Saison {team.active_season} • Rennen {team.current_race}")
    return embed


# ─── Driver Embed ──────────────────────────────────────────────────────────

def driver_embed(driver: Driver, team_name: str = "Unbekannt") -> Embed:
    embed = Embed(
        title=f"{E['driver']} {driver.full_name}",
        colour=C["info"],
        description=f"{driver.nationality} • {driver.age} Jahre • "
                    f"{_driver_rating_stars(driver.attributes.overall())}",
    )

    # Attributes with bars
    attrs_text = ""
    for attr in ["speed", "consistency", "racecraft", "overtaking",
                  "tyre_management", "qualifying_pace", "wet_performance",
                  "mental_strength"]:
        val = getattr(driver.attributes, attr)
        label = attr.replace("_", " ").title()
        attrs_text += f"{label:20s} {_attribute_bar(val)} {val:2d}\n"
    embed.add_field(name="Attribute", value=f"```{attrs_text}```", inline=False)

    # Hidden stats
    hidden_text = (
        f"Potential: {driver.hidden.potential}\n"
        f"Growth: {driver.hidden.growth_rate:.1f}x\n"
        f"Aggression: {driver.hidden.aggression}/100\n"
        f"Risk: {driver.hidden.risk_taking}/100\n"
        f"Druck: {driver.hidden.pressure_handling}/100"
    )
    embed.add_field(name="Versteckte Stats", value=hidden_text, inline=True)

    # Personality
    p_mods = {
        "calm": "🧘 Gleichmäßig, selten Fehler",
        "aggressive": "🔥 Maximales Risiko, viele Überholmanöver",
        "inconsistent": "🎭 Mal Weltklasse, mal Katastrophe",
        "strategic": "🧠 Exzellentes Racecraft & Reifenmanagement",
        "clutch": "💎 Liefert unter Druck Höchstleistungen",
    }
    p_desc = p_mods.get(driver.personality.value, driver.personality.value)
    embed.add_field(name=f"Persönlichkeit: {driver.personality.value.title()}", value=p_desc, inline=False)

    # Career
    embed.add_field(name="Team", value=team_name, inline=True)
    embed.add_field(name="Moral", value=f"{driver.morale}/100", inline=True)
    embed.add_field(name="Rennen", value=str(driver.races_driven), inline=True)
    embed.add_field(name="Siege", value=str(driver.wins), inline=True)
    embed.add_field(name="Podien", value=str(driver.podiums), inline=True)

    return embed


# ─── Race Result Embed ─────────────────────────────────────────────────────

def race_embed(result: RaceResult, team: Team) -> Embed:
    embed = Embed(
        title=f"{E['f1']} Rennen {result.race_number} — {result.track_name}",
        colour=C["primary"],
        description=f"{_weather_icon(result.weather)} {result.weather.value.upper()} "
                    f"• Saison {result.season}",
    )

    for i, driver_result in enumerate([result.driver_1_result, result.driver_2_result], 1):
        if driver_result:
            driver = team.main_driver_1 if i == 1 else team.main_driver_2
            name = driver.full_name if driver else f"Driver #{i}"
            status = "💥 DNF" if driver_result.dnfs else f"P{driver_result.position}"
            time_s = driver_result.total_time_ms / 1000
            embed.add_field(
                name=f"{'🥇' if driver_result.position == 1 else '🥈' if driver_result.position == 2 else '🥉' if driver_result.position == 3 else i} {name}",
                value=f"{status} • {time_s:.3f}s",
                inline=True,
            )

    embed.add_field(name=f"{E['money']} Punkte", value=str(result.team_points), inline=True)

    if result.race_events:
        events_text = "\n".join(result.race_events[:5])
        embed.add_field(name="📰 Ereignisse", value=events_text[:1024], inline=False)

    return embed


# ─── Qualifier Embed ───────────────────────────────────────────────────────

def qualifier_embed(result: QualifierResult, team: Team) -> Embed:
    d1 = team.main_driver_1
    d2 = team.main_driver_2
    d3 = team.reserve_driver

    embed = Embed(
        title=f"{E['qualifier']} Qualifier — Rennen {result.race_number}",
        colour=C["info"],
        description=f"Liga F{result.league} • Saison {result.season}\n"
                    f"Team: {team.name}",
    )

    for i, (d, time) in enumerate([
        (d1, result.driver_1_time_ms),
        (d2, result.driver_2_time_ms),
        (d3, result.driver_3_time_ms),
    ], 1):
        name = d.full_name if d else f"Fahrer {i}"
        label = "MAIN" if i <= 2 else "RES"
        embed.add_field(
            name=f"{label} {name}",
            value=f"{time/1000:.3f}s",
            inline=True,
        )

    if result.was_auto:
        embed.add_field(
            name="⚠️ Automatisch",
            value="Standardzeit verwendet (AFK)",
            inline=False,
        )

    embed.add_field(
        name="🏁 ⌀ Teamzeit",
        value=f"**{result.average_time_ms/1000:.3f}s**",
        inline=False,
    )

    return embed


# ─── Ranking Embed ─────────────────────────────────────────────────────────

def ranking_embed(rankings: list[TeamRank], league: int) -> Embed:
    embed = Embed(
        title=f"{_league_icon(league)} F{league} RANKING",
        colour=C["gold"],
        description=f"Endstand der Saison — {len(rankings)} Teams",
    )

    lines = []
    for r in rankings:
        icon = "🥇" if r.rank == 1 else "🥈" if r.rank == 2 else "🥉" if r.rank == 3 else f"#{r.rank}"
        total = r.total_time_ms / 1000
        avg = r.average_time_ms / 1000
        lines.append(f"{icon} **{r.team_name}** — {total:.3f}s (⌀ {avg:.3f}s)")

    for chunk in [lines[i:i+10] for i in range(0, len(lines), 10)]:
        embed.add_field(
            name="\u200b",
            value="\n".join(chunk),
            inline=False,
        )
    return embed


# ─── Promotion/Relegation Embed ────────────────────────────────────────────

def promotion_embed(rankings: list[TeamRank], league: int) -> Embed:
    embed = Embed(
        title=f"{E['up']} PROMOTION / {E['down']} RELEGATION F{league}",
        colour=C["warning"],
    )

    if len(rankings) >= 2:
        promote = rankings[:2]
        embed.add_field(
            name=f"{E['up']} Promotion → F{league - 1}",
            value="\n".join(f"✅ {r.team_name}" for r in promote),
            inline=True,
        )

    if len(rankings) >= 2:
        relegate = rankings[-2:]
        embed.add_field(
            name=f"{E['down']} Relegation → F{league + 1}",
            value="\n".join(f"❌ {r.team_name}" for r in relegate),
            inline=True,
        )

    return embed


# ─── Driver Market Embed ───────────────────────────────────────────────────

def market_embed(drivers: list[Driver], page: int = 1) -> Embed:
    embed = Embed(
        title=f"{E['driver']} Transfermarkt",
        colour=C["info"],
        description=f"Seite {page} — {len(drivers)} verfügbare Fahrer",
    )

    for d in drivers[:10]:
        stars = _driver_rating_stars(d.attributes.overall())
        embed.add_field(
            name=f"{d.full_name} ({d.nationality}) {stars}",
            value=f"Alter: {d.age} • OVR: {d.attributes.overall():.1f} • "
                  f"Pers: {d.personality.value}",
            inline=False,
        )
    return embed


# ─── Event Embed ───────────────────────────────────────────────────────────

def event_embed(events: list[WorldEvent]) -> Embed:
    embed = Embed(
        title="📰 Welt-Ereignisse",
        colour=C["warning"],
    )
    for e in events[:5]:
        embed.add_field(name=e.event_type.replace("_", " ").title(),
                        value=e.description[:256], inline=False)
    return embed


# ─── Help Embed ────────────────────────────────────────────────────────────

def help_embed() -> Embed:
    embed = Embed(
        title=f"{E['f1']} DISCORD MOTORSPORT UNIVERSE",
        colour=C["primary"],
        description="Dein Motorsport-Management-System. "
                    "Verwalte Teams, fahre Rennen, steige auf!",
    )

    commands = {
        "🏁 Team": "`/team` `/team lineup` `/team upgrade`",
        "🏎️ Rennen": "`/race` `/race result`",
        "👤 Fahrer": "`/drivers` `/driver <id>` `/train`",
        "⏱️ Qualifier": "`/qualifier` `/qualifier run` `/qualifier ranking`",
        "💰 Wirtschaft": "`/market` `/market buy` `/sponsor`",
        "📊 Saison": "`/season` `/season standings`",
        "🎓 Academy": "`/academy` `/academy scout`",
        "🏆 Ligen": "`/league` `/league ranking`",
        "⭐ Premium": "`/premium` `/premium status`",
    }

    for name, cmds in commands.items():
        embed.add_field(name=name, value=cmds, inline=True)

    embed.set_footer(text="Powered by Hermes Agent • Kein Pay-to-Win")
    return embed
