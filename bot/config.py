"""
Bot configuration — all settings from environment variables with defaults.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    # Discord
    token: str = os.getenv("DISCORD_TOKEN", "")
    guild_id: int = int(os.getenv("GUILD_ID", "0"))
    prefix: str = "/"

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./motorsport.db"
    )

    # Game settings
    races_per_season: int = int(os.getenv("RACES_PER_SEASON", "14"))
    qualifier_window_hours: int = int(os.getenv("QUALIFIER_WINDOW_HOURS", "24"))
    seed: int = int(os.getenv("SIMULATION_SEED", "0")) or None

    # Deployment
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Colors for embeds
    colors: dict = field(default_factory=lambda: {
        "primary": 0xE10600,        # Ferrari Red
        "success": 0x00FF00,
        "warning": 0xFFAA00,
        "error": 0xFF0000,
        "info": 0x3498DB,
        "gold": 0xFFD700,
        "silver": 0xC0C0C0,
        "bronze": 0xCD7F32,
    })

    # Emoji mappings
    emojis: dict = field(default_factory=lambda: {
        "f1": "🏁",
        "driver": "🏎️",
        "team": "🏆",
        "money": "💰",
        "star": "⭐",
        "up": "🚀",
        "down": "⬇️",
        "academy": "🎓",
        "event": "📰",
        "qualifier": "⏱️",
        "weather": "🌤️",
        "rain": "🌧️",
        "storm": "⛈️",
    })
