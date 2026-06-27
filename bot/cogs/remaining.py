"""Season, Market, Sponsor, Academy, League, Admin cogs (light stubs)."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.data.repository import TeamRepo, DriverRepo, PlayerRepo
from motorsport.data.database import get_session_maker


class SeasonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="season", description="Saison-Status")
    async def season_status(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
        if not teams:
            await interaction.response.send_message("❌ Kein Team")
            return
        t = teams[0]
        embed = discord.Embed(
            title=f"📅 Saison {t.active_season}",
            colour=0x3498DB,
            description=f"Rennen {t.current_race}/12 • Liga F{t.league}",
        )
        embed.add_field(name="Punkte", value=str(t.season_points))
        embed.add_field(name="Siege", value=str(t.wins))
        embed.add_field(name="Podien", value=str(t.podiums))
        embed.add_field(name="Budget", value=f"${float(t.budget):,.0f}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="season_standings", description="Saison-Tabelle")
    async def season_standings(self, interaction: discord.Interaction):
        await interaction.response.send_message("📊 Season Standings werden geladen...", ephemeral=True)


class MarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="market", description="Transfermarkt durchsuchen")
    async def market(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            free_agents = await DriverRepo.get_free_agents(session)
        if not free_agents:
            await interaction.response.send_message("📭 Keine Free Agents verfügbar")
            return
        embed = discord.Embed(title="🏪 Transfermarkt", colour=0x3498DB,
                             description=f"{len(free_agents)} Free Agents")
        for d in free_agents[:10]:
            ovr = (d.speed + d.consistency + d.racecraft + d.overtapping +
                   d.tyre_management + d.qualifying_pace + d.wet_performance +
                   d.mental_strength) / 8
            embed.add_field(
                name=f"{d.first_name} {d.last_name} ({d.nationality})",
                value=f"Alter: {d.age} • OVR: {ovr:.1f} • ID: `{d.id[:8]}...`",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="market_buy", description="Free Agent kaufen")
    @app_commands.describe(driver_id="Fahrer-ID")
    async def market_buy(self, interaction: discord.Interaction, driver_id: str):
        await interaction.response.send_message("⚙️ Transfer wird implementiert...")


class SponsorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sponsor", description="Sponsor-Übersicht")
    async def sponsor(self, interaction: discord.Interaction):
        embed = discord.Embed(title="💰 Sponsor-Übersicht", colour=0xFFD700,
                             description="Sponsoren-System wird geladen...")
        await interaction.response.send_message(embed=embed)


class AcademyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="academy", description="Academy-Übersicht")
    async def academy(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎓 Academy-System wird geladen...")

    @app_commands.command(name="academy_scout", description="Scout einsetzen")
    @app_commands.describe(region="Region (europe, asia, etc.)")
    async def academy_scout(self, interaction: discord.Interaction, region: str = None):
        await interaction.response.send_message(f"🔍 Scout wird in {region or 'global'} eingesetzt...")


class LeagueCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="league", description="Liga-Info")
    async def league_info(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Ligen-Übersicht", colour=0xE10600,
                             description="10 Ligen: F1 (Top) → F10 (Einstieg)")
        for i in range(1, 11):
            icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
            embed.add_field(name=f"{icon} F{i}", value=f"{10} Teams", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="league_ranking", description="Globales Ranking")
    async def league_ranking(self, interaction: discord.Interaction):
        await interaction.response.send_message("📊 Globales Ranking wird geladen...")


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="admin_simulate", description="[Admin] Simuliere nächste Runde")
    @app_commands.default_permissions(administrator=True)
    async def admin_simulate(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚙️ Admin: Season-Tick wird ausgeführt...", ephemeral=True)
