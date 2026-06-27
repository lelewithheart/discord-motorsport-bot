"""
Main Discord bot entry point for Motorsport Universe.
Includes Railway-compatible health check server.
"""
from __future__ import annotations
import os
import sys
import asyncio
import logging
from threading import Thread

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

cfg = BotConfig()


# ─── Railway Health Check Server ──────────────────────────────────────
# Railway needs a port-binding service, otherwise it kills the container.
# This tiny HTTP server satisfies Railway's health check on $PORT.

def start_health_server():
    """Start a minimal HTTP server for Railway health checks."""
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Motorsport Bot is running")

            def log_message(self, format, *args):
                pass  # suppress HTTP log spam

        server = HTTPServer((host, port), HealthHandler)
        log.info(f"✅ Health server listening on {host}:{port}")
        server.serve_forever()
    except Exception as e:
        log.warning(f"⚠️ Health server could not start on {host}:{port}: {e}")


# ─── Discord Bot ──────────────────────────────────────────────────────

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
        try:
            await init_db()
            log.info("✅ Database initialized")
        except Exception as e:
            log.error(f"❌ Database init failed: {e}")
            raise

        # Load cogs
        cogs = [
            TeamCog, RaceCog, DriverCog, QualifierCog,
            SeasonCog, MarketCog, SponsorCog, AcademyCog,
            LeagueCog, AdminCog, GeneralCog,
        ]
        for cog_cls in cogs:
            try:
                await self.add_cog(cog_cls(self))
                log.info(f"✅ Loaded cog: {cog_cls.__name__}")
            except Exception as e:
                log.error(f"❌ Failed to load {cog_cls.__name__}: {e}")

        # Sync slash commands
        try:
            if cfg.guild_id:
                guild = discord.Object(id=cfg.guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                log.info(f"✅ Synced commands to guild {cfg.guild_id}")
            else:
                await self.tree.sync()
                log.info("✅ Synced commands globally (may take up to 1 hour)")
        except Exception as e:
            log.warning(f"⚠️ Command sync failed (will retry): {e}")

    async def on_ready(self):
        log.info(f"✅ Bot online: {self.user} (ID: {self.user.id})")
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="F1 | /help"
        )
        await self.change_presence(activity=activity)


async def main():
    # Validate token
    if not cfg.token:
        log.error("❌ DISCORD_TOKEN is not set!")
        log.error("   Set it in your environment variables and restart.")
        return

    log.info(f"🚀 Starting Motorsport Bot...")
    log.info(f"   Token: {cfg.token[:8]}...{cfg.token[-4:]}")
    log.info(f"   Guild ID: {cfg.guild_id or 'global (slow sync)'}")
    log.info(f"   Database: {cfg.database_url}")

    # Start Railway health check in background thread
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # Connect Discord bot
    bot = MotorsportBot()
    try:
        async with bot:
            await bot.start(cfg.token)
    except discord.LoginFailure:
        log.error("❌ Login failed! Check your DISCORD_TOKEN.")
    except Exception as e:
        log.error(f"❌ Bot crashed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
