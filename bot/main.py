"""
Main Discord bot entry point for Motorsport Universe.
"""
from __future__ import annotations
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import discord
from discord.ext import commands
from bot.config import BotConfig
from bot.cogs import (
    TeamCog, RaceCog, DriverCog, QualifierCog,
    SeasonCog, MarketCog, SponsorCog, AcademyCog,
    LeagueCog, AdminCog, GeneralCog,
)
from motorsport.data.database import init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

cfg = BotConfig()


class MotorsportBot(commands.Bot):
    """Main bot class for Motorsport Universe."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=cfg.prefix,
            intents=intents,
            help_command=None,
        )
        self.config = cfg

    async def setup_hook(self):
        """Initialize database and load cogs."""
        # Initialize database
        await init_db()
        log.info("✅ Database initialized")

        # Load cogs
        cogs = [
            TeamCog, RaceCog, DriverCog, QualifierCog,
            SeasonCog, MarketCog, SponsorCog, AcademyCog,
            LeagueCog, AdminCog, GeneralCog,
        ]
        for cog_cls in cogs:
            await self.add_cog(cog_cls(self))
            log.info(f"✅ Loaded cog: {cog_cls.__name__}")

        # Sync slash commands
        if cfg.guild_id:
            guild = discord.Object(id=cfg.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info(f"✅ Synced commands to guild {cfg.guild_id}")
        else:
            await self.tree.sync()
            log.info("✅ Synced commands globally")

    async def on_ready(self):
        log.info(f"✅ Bot ready: {self.user} (ID: {self.user.id})")
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="F1 | /help"
        )
        await self.change_presence(activity=activity)


async def main():
    bot = MotorsportBot()
    async with bot:
        await bot.start(cfg.token)


if __name__ == "__main__":
    asyncio.run(main())
