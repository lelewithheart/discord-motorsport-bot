"""Season, Market, Sponsor, Academy, League, Admin cogs."""
from __future__ import annotations
import random
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.data.repository import TeamRepo, DriverRepo, PlayerRepo
from motorsport.data.database import get_session_maker
from bot.views.paginator import Paginator


# ─── Season ──────────────────────────────────────────────────────────────────


class SeasonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="season", description="Saison-Status")
    async def season_status(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
        if not teams:
            await interaction.response.send_message("❌ Kein Team", ephemeral=True)
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
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="season_standings", description="Saison-Tabelle")
    async def season_standings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            t = teams[0]
            all_teams = await TeamRepo.get_by_league(session, t.league)

        sorted_teams = sorted(all_teams, key=lambda x: (-x.season_points, -x.wins))
        embeds = []
        for i, chunk in enumerate([sorted_teams[j:j+10] for j in range(0, len(sorted_teams), 10)]):
            embed = discord.Embed(
                title=f"📊 F{t.league} — Saison {t.active_season}",
                colour=0x3498DB,
            )
            lines = []
            for rank, te in enumerate(chunk, 1 + i * 10):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
                hl_s = "**" if te.id == t.id else ""
                hl_e = "**" if te.id == t.id else ""
                lines.append(
                    f"{medal} {hl_s}{te.name}{hl_e} — {te.season_points} Pkt | {te.wins} S | {te.podiums} P"
                )
            embed.description = "\n".join(lines)
            embeds.append(embed)

        if len(embeds) == 1:
            await interaction.followup.send(embed=embeds[0])
        else:
            await interaction.followup.send(embed=embeds[0], view=Paginator(embeds, user_id=interaction.user.id))


# ─── Market ──────────────────────────────────────────────────────────────────


class MarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="market", description="Transfermarkt durchsuchen")
    async def market(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            free_agents = await DriverRepo.get_free_agents(session)

        if not free_agents:
            await interaction.followup.send("📭 Keine Free Agents verfügbar")
            return

        per_page = 10
        pages = []
        for i in range(0, len(free_agents), per_page):
            chunk = free_agents[i:i + per_page]
            embed = discord.Embed(
                title="🏪 Transfermarkt",
                colour=0x3498DB,
                description=f"📦 {len(free_agents)} Free Agents — Seite {i // per_page + 1}/{(len(free_agents) + per_page - 1) // per_page}",
            )
            for d in chunk:
                ovr = (d.speed + d.consistency + d.racecraft + d.overtaking +
                       d.tyre_management + d.qualifying_pace + d.wet_performance +
                       d.mental_strength) / 8
                embed.add_field(
                    name=f"{d.first_name} {d.last_name} ({d.nationality})",
                    value=f"Alter: {d.age} • OVR: {ovr:.1f} • ID: `{d.id[:8]}...`",
                    inline=False,
                )
            embed.set_footer(text=f"Gesamt: {len(free_agents)} Free Agents")
            pages.append(embed)

        if len(pages) == 1:
            await interaction.followup.send(embed=pages[0])
        else:
            await interaction.followup.send(embed=pages[0], view=Paginator(pages, user_id=interaction.user.id))

    @app_commands.command(name="market_buy", description="Free Agent kaufen")
    @app_commands.describe(driver_id="Fahrer-ID")
    async def market_buy(self, interaction: discord.Interaction, driver_id: str):
        await interaction.response.send_message("⚙️ Transfer wird implementiert...", ephemeral=True)


# ─── Sponsor ─────────────────────────────────────────────────────────────────


class SponsorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="sponsor", description="Sponsor-Übersicht")
    async def sponsor(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)

        if not teams:
            await interaction.followup.send("❌ Kein Team")
            return

        t = teams[0]
        embed = discord.Embed(
            title="💰 Sponsor-Übersicht",
            colour=0xFFD700,
        )
        embed.add_field(name="Team", value=t.name, inline=False)
        embed.add_field(
            name="Aktives Sponsoring",
            value=f"${float(t.sponsor_income):,.0f}/Rennen" if t.sponsor_income and float(t.sponsor_income) > 0 else "❌ Kein aktiver Sponsor",
            inline=False,
        )
        embed.add_field(name="Budget", value=f"${float(t.budget):,.0f}")
        embed.add_field(name="Prize Money", value=f"${float(t.prize_money):,.0f}")
        embed.add_field(name="Liga", value=f"F{t.league}")
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="🏁 Statistiken", value=f"Siege: {t.wins} • Podien: {t.podiums} • Punkte: {t.season_points}")

        await interaction.followup.send(embed=embed)


# ─── Academy ─────────────────────────────────────────────────────────────────


class AcademySelect(discord.ui.Select):
    """Region selector for academy scouting."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Europa", value="europe", emoji="🌍",
                                 description="Europäische Talente"),
            discord.SelectOption(label="Asien", value="asia", emoji="🌏",
                                 description="Asiatische Talente"),
            discord.SelectOption(label="Amerika", value="americas", emoji="🌎",
                                 description="Amerikanische Talente"),
            discord.SelectOption(label="Global", value="global", emoji="🌐",
                                 description="Weltweite Suche"),
        ]
        super().__init__(
            placeholder="🌍 Scout-Region wählen...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        region = self.values[0]
        region_names = {
            "europe": "Europa",
            "asia": "Asien",
            "americas": "Amerika",
            "global": "Global",
        }
        region_emojis = {
            "europe": "🌍",
            "asia": "🌏",
            "americas": "🌎",
            "global": "🌐",
        }

        # Generate placeholder scouting results
        first_names = {
            "europe": ["Max", "Liam", "Noah", "Emma", "Oliver", "Sophia", "Lukas", "Marie", "Felix", "Elena"],
            "asia": ["Hiro", "Yuki", "Sakura", "Takashi", "Mei", "Kenji", "Aiko", "Ryo", "Hana", "Satoshi"],
            "americas": ["Lucas", "Sophia", "Mateo", "Isabella", "Diego", "Valentina", "Ethan", "Mia", "Carlos", "Emma"],
            "global": ["Kai", "Lena", "Ravi", "Zara", "Omar", "Nia", "Ivan", "Suki", "Leo", "Aria"],
        }
        last_names = {
            "europe": ["Schmidt", "Mueller", "Rossi", "Johansson", "Dubois", "Andersen", "Varga", "Petrov", "Fischer", "Garcia"],
            "asia": ["Tanaka", "Watanabe", "Suzuki", "Kim", "Chen", "Yamamoto", "Park", "Li", "Sato", "Wang"],
            "americas": ["Silva", "Martinez", "Gonzalez", "Oliveira", "Lopez", "Pereira", "Rodriguez", "Ferreira", "Costa", "Santos"],
            "global": ["Patel", "Okafor", "Cohen", "Singh", "Abdullah", "Ndlovu", "Johansson", "Osei", "Bouchard", "Nakamura"],
        }

        drivers_data = []
        for i in range(5):
            fname = random.choice(first_names[region])
            lname = random.choice(last_names[region])
            age = random.randint(16, 19)
            ovr = round(random.uniform(40, 85), 1)
            potential = random.randint(55, 95)
            nationality = region.upper()[:4]
            drivers_data.append((fname, lname, age, ovr, potential, nationality))

        embed = discord.Embed(
            title=f"{region_emojis[region]} Scout-Ergebnisse — {region_names[region]}",
            colour=0x00FF88,
            description="🔍 **Scout gesendet!** Folgende Talente wurden gefunden:\n",
        )
        lines = []
        for fname, lname, age, ovr, potential, nat in drivers_data:
            lines.append(f"👤 **{fname} {lname}** ({nat}) • Alter: {age} • OVR: {ovr} • Potenzial: {potential}")
        embed.description += "\n".join(lines)
        embed.set_footer(text="Nutze /academy um Talente ins Team zu holen")

        # Disable the dropdown after selection
        self.disabled = True
        await interaction.response.edit_message(embed=embed, view=self.view)


class AcademySelectView(discord.ui.View):
    """View wrapping the academy region selector."""

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(AcademySelect())


class AcademyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="academy", description="Academy-Übersicht")
    async def academy(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            t = teams[0]
            all_drivers = await DriverRepo.get_by_team(session, t.id)

        academy_drivers = [d for d in all_drivers if d.is_academy]

        if not academy_drivers:
            embed = discord.Embed(
                title="🎓 Academy-Übersicht",
                colour=0x00FF88,
                description="Keine Academy-Fahrer in deinem Team.\n"
                            "Nutze `/academy_scout` um neue Talente zu entdecken!",
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🎓 Academy — {t.name}",
            colour=0x00FF88,
            description=f"📋 {len(academy_drivers)} Academy-Fahrer\n",
        )
        for d in academy_drivers:
            ovr = (d.speed + d.consistency + d.racecraft + d.overtaking +
                   d.tyre_management + d.qualifying_pace + d.wet_performance +
                   d.mental_strength) / 8
            embed.add_field(
                name=f"{d.first_name} {d.last_name}",
                value=f"🇺🇳 {d.nationality} • Alter: {d.age} • OVR: {ovr:.1f}",
                inline=False,
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="academy_scout", description="Scout einsetzen")
    @app_commands.describe(region="Region (europe, asia, americas, global)")
    async def academy_scout(self, interaction: discord.Interaction, region: str = None):
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return

        if region:
            # Direct region parameter — show results inline
            region_names = {
                "europe": "Europa", "asia": "Asien", "americas": "Amerika", "global": "Global",
            }
            region_emojis = {
                "europe": "🌍", "asia": "🌏", "americas": "🌎", "global": "🌐",
            }
            if region not in region_names:
                await interaction.followup.send(
                    "❌ Unbekannte Region. Verfügbar: `europe`, `asia`, `americas`, `global`"
                )
                return

            embed = discord.Embed(
                title=f"{region_emojis[region]} Scout-Ergebnisse — {region_names[region]}",
                colour=0x00FF88,
                description="🔍 **Scout gesendet!** Warte auf Ergebnisse..."
            )
            embed.set_footer(text="Nutze /academy um Talente ins Team zu holen")
            await interaction.followup.send(embed=embed)
        else:
            # No region specified — show select menu
            embed = discord.Embed(
                title="🌍 Academy Scout",
                colour=0x00FF88,
                description="Wähle eine Region für die Talentsuche:",
            )
            await interaction.followup.send(embed=embed, view=AcademySelectView())


# ─── League ──────────────────────────────────────────────────────────────────


class LeagueCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="league", description="Liga-Info")
    async def league_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏆 Ligen-Übersicht",
            colour=0xE10600,
            description="10 Ligen: F1 (Top) → F10 (Einstieg)",
        )
        for i in range(1, 11):
            icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
            embed.add_field(name=f"{icon} F{i}", value=f"{10} Teams", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="league_ranking", description="Globales Ranking")
    async def league_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            t = teams[0]
            all_teams = await TeamRepo.get_by_league(session, t.league)

        sorted_teams = sorted(all_teams, key=lambda x: (-x.season_points, -x.wins))
        embed = discord.Embed(
            title=f"🌍 Globales Ranking — F{t.league}",
            colour=0xE10600,
        )
        lines = []
        for rank, te in enumerate(sorted_teams, 1):
            hl_s = "**" if te.id == t.id else ""
            hl_e = "**" if te.id == t.id else ""
            lines.append(f"#{rank} {hl_s}{te.name}{hl_e} — {te.season_points} Pkt")
        embed.description = "\n".join(lines[:20])
        if len(sorted_teams) > 20:
            embed.set_footer(text=f"Zeige Top 20 von {len(sorted_teams)} Teams")
        await interaction.followup.send(embed=embed)


# ─── Admin ───────────────────────────────────────────────────────────────────


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="admin_simulate", description="[Admin] Simuliere nächste Runde")
    @app_commands.default_permissions(administrator=True)
    async def admin_simulate(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.followup.send("❌ Kein Team")
                return
            t = teams[0]

        # Build a realistic-looking simulated race result
        tracks = [
            "Monza", "Silverstone", "Spa", "Monaco", "Suzuka", "Interlagos",
            "Melbourne", "Bahrain", "Singapore", "Austin", "Montreal",
            "Abu Dhabi", "Barcelona", "Zandvoort", "Imola", "Red Bull Ring",
        ]
        weathers = ["☀️ Trocken", "⛅ Bewölkt", "🌦️ Leichter Regen", "🌧️ Starker Regen", "⛈️ Sturm"]
        positions = [random.randint(1, 20) for _ in range(2)]
        points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        team_points = sum(points_map.get(p, 0) for p in positions)

        track = random.choice(tracks)
        weather = random.choice(weathers)

        embed = discord.Embed(
            title="🏁 Administrativer Rennsimulator",
            colour=0xE74C3C,
            description="⚙️ **Admin: Nächstes Rennen wird simuliert...**\n"
                        f"✅ Simulation abgeschlossen!\n",
        )
        embed.add_field(name="📍 Strecke", value=track, inline=True)
        embed.add_field(name="🌦️ Wetter", value=weather, inline=True)
        embed.add_field(name="🏎️ Team", value=t.name, inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(
            name="Fahrer 1 — Position",
            value=f"**P{positions[0]}** — {points_map.get(positions[0], 0)} Pkt",
            inline=True,
        )
        embed.add_field(
            name="Fahrer 2 — Position",
            value=f"**P{positions[1]}** — {points_map.get(positions[1], 0)} Pkt",
            inline=True,
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="🏆 Team-Punkte", value=f"+{team_points}", inline=True)
        embed.add_field(name="📊 Gesamtpunkte", value=t.season_points + team_points, inline=True)
        embed.set_footer(text="Admin-Simulation • Nur für Admins sichtbar")

        await interaction.followup.send(embed=embed)


# ─── Setup ───────────────────────────────────────────────────────────────────


async def setup(bot: commands.Bot):
    await bot.add_cog(SeasonCog(bot))
    await bot.add_cog(MarketCog(bot))
    await bot.add_cog(SponsorCog(bot))
    await bot.add_cog(AcademyCog(bot))
    await bot.add_cog(LeagueCog(bot))
    await bot.add_cog(AdminCog(bot))
