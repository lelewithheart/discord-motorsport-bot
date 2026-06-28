"""Team commands cog."""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from motorsport.models import Team, Driver, DriverSlot, UpgradeType, UPGRADE_COSTS
from motorsport.simulation.driver_generator import DriverGenerator
from motorsport.data.repository import TeamRepo, DriverRepo, PlayerRepo
from motorsport.data.models import TeamUpgradeModel
from motorsport.data.database import get_session_maker
from bot.embeds import team_embed
from sqlalchemy import select


class TeamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session_maker = get_session_maker()

    @app_commands.command(name="team", description="Deine Team-Übersicht")
    async def team_overview(self, interaction: discord.Interaction):
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
        if not teams:
            embed = discord.Embed(
                title="Kein Team",
                description="Du hast noch kein Team. Erstelle eines mit `/team create`",
                colour=0xFFAA00,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Convert DB model to dataclass for embed
        db_team = teams[0]
        team = await self._db_to_team(db_team, session)
        embed = team_embed(team)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="team_create", description="Erstelle ein neues Team")
    @app_commands.describe(name="Team-Name")
    async def team_create(self, interaction: discord.Interaction, name: str):
        async with self.session_maker() as session:
            player = await PlayerRepo.get_or_create(session, interaction.user.id,
                                                     interaction.user.name)
            existing = await TeamRepo.get_by_owner(session, interaction.user.id)
            if len(existing) >= (3 if player.is_premium else 1):
                embed = discord.Embed(
                    title="❌ Limit erreicht",
                    description=f"Maximal {'3' if player.is_premium else '1'} Teams erlaubt. "
                                f"{'⭐ Premium' if not player.is_premium else ''}",
                    colour=0xFF0000,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            team = await TeamRepo.create(session, interaction.user.id, name)

            # Generate 3 initial drivers
            gen = DriverGenerator()
            for slot, is_academy in [(1, False), (2, False), (3, True)]:
                d = gen.generate_driver(
                    age=18 + slot * 2,
                    is_academy=is_academy,
                )
                await DriverRepo.create(session, {
                    "id": d.id,
                    "team_id": team.id,
                    "first_name": d.first_name,
                    "last_name": d.last_name,
                    "nationality": d.nationality,
                    "age": d.age,
                    "speed": d.attributes.speed,
                    "consistency": d.attributes.consistency,
                    "racecraft": d.attributes.racecraft,
                    "overtaking": d.attributes.overtaking,
                    "tyre_management": d.attributes.tyre_management,
                    "qualifying_pace": d.attributes.qualifying_pace,
                    "wet_performance": d.attributes.wet_performance,
                    "mental_strength": d.attributes.mental_strength,
                    "potential": d.hidden.potential,
                    "growth_rate": d.hidden.growth_rate,
                    "aggression": d.hidden.aggression,
                    "risk_taking": d.hidden.risk_taking,
                    "pressure_handling": d.hidden.pressure_handling,
                    "personality": d.personality.value,
                    "slot": slot,
                    "is_academy": is_academy,
                    "morale": d.morale,
                })

            # Generate race schedule for this season if not exists
            from motorsport.data.repository import RaceScheduleRepo, TrackRepo
            existing_schedule = await RaceScheduleRepo.get_by_season(
                session, team.active_season
            )
            if not existing_schedule:
                await TrackRepo.seed_if_empty(session)
                all_tracks = await TrackRepo.get_all(session)
                if all_tracks:
                    await RaceScheduleRepo.generate_schedule(
                        session, team.active_season, all_tracks
                    )

        embed = discord.Embed(
            title="✅ Team erstellt!",
            description=f"**{name}** ist bereit für die F10-Liga!",
            colour=0x00FF00,
        )
        embed.add_field(name="Fahrer", value="3 Fahrer generiert (2 Haupt + 1 Reserve)")
        embed.add_field(name="Budget", value="$1,000,000")
        embed.add_field(name="Nächster Schritt", value="`/team` für Übersicht")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="team_lineup", description="Aufstellung ändern")
    @app_commands.describe(driver_1="Fahrer-ID für Slot 1",
                           driver_2="Fahrer-ID für Slot 2",
                           reserve="Fahrer-ID für Reserve")
    async def team_lineup(self, interaction: discord.Interaction,
                          driver_1: str = None, driver_2: str = None,
                          reserve: str = None):
        await interaction.response.send_message(
            "⚙️ Aufstellungs-Änderung ist im Aufbau. "
            "Nutze `/drivers` um Fahrer-IDs zu sehen.",
            ephemeral=True
        )

    @app_commands.command(name="team_upgrade", description="Team-Upgrade kaufen")
    async def team_upgrade(self, interaction: discord.Interaction):
        """Interactive upgrade system with select menu."""
        async with self.session_maker() as session:
            teams = await TeamRepo.get_by_owner(session, interaction.user.id)
            if not teams:
                await interaction.response.send_message("❌ Kein Team", ephemeral=True)
                return

            db_team = teams[0]

            # Get current upgrade levels from DB
            result = await session.execute(
                select(TeamUpgradeModel).where(TeamUpgradeModel.team_id == db_team.id)
            )
            existing_upgrades = {u.upgrade_type: u.level for u in result.scalars().all()}

            options = []
            for ut in UpgradeType:
                current_level = existing_upgrades.get(ut.value, 0)
                costs = UPGRADE_COSTS.get(ut, [])
                if current_level < len(costs):
                    cost = costs[current_level]
                    label = f"{ut.value.title()} — Lv.{current_level + 1} (${cost:,})"
                    options.append(discord.SelectOption(
                        label=label[:100],
                        value=ut.value,
                        description=f"Aktuell: Lv.{current_level} → Lv.{current_level + 1}",
                    ))
                else:
                    options.append(discord.SelectOption(
                        label=f"✅ {ut.value.title()} — MAX LEVEL",
                        value=ut.value,
                        default=True,
                    ))

        if not any(o.value for o in options if not o.default):
            await interaction.response.send_message(
                "🏆 Alle Upgrades sind bereits auf Maximallevel!", ephemeral=True
            )
            return

        view = UpgradeSelectView(options, db_team.id, interaction.user.id, self.session_maker)
        embed = discord.Embed(
            title="🔧 Team-Upgrades",
            colour=0x00FF00,
            description=f"Wähle ein Upgrade für dein Team.\nBudget: ${float(db_team.budget):,.0f}",
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _db_to_team(self, db_team, session):
        """Convert DB model to dataclass Team for embed rendering."""
        db_drivers = await DriverRepo.get_by_team(session, db_team.id)

        team = Team(
            id=db_team.id,
            name=db_team.name,
            owner_id=db_team.owner_id,
            league=db_team.league,
            budget=db_team.budget,
            performance_rating=db_team.performance_rating,
            infrastructure_level=db_team.infrastructure_level,
            wins=db_team.wins,
            podiums=db_team.podiums,
            season_points=db_team.season_points,
            total_qualifier_time_ms=db_team.total_qualifier_time_ms,
            qualifier_count=db_team.qualifier_count,
            is_premium=db_team.is_premium,
            active_season=db_team.active_season,
            current_race=db_team.current_race,
        )

        from motorsport.models import Personality, DriverAttributes, HiddenStats

        for db_d in db_drivers:
            d = Driver(
                id=db_d.id,
                first_name=db_d.first_name,
                last_name=db_d.last_name,
                nationality=db_d.nationality,
                age=db_d.age,
                attributes=DriverAttributes(
                    speed=db_d.speed, consistency=db_d.consistency,
                    racecraft=db_d.racecraft, overtaking=db_d.overtaking,
                    tyre_management=db_d.tyre_management,
                    qualifying_pace=db_d.qualifying_pace,
                    wet_performance=db_d.wet_performance,
                    mental_strength=db_d.mental_strength,
                ),
                hidden=HiddenStats(
                    potential=db_d.potential, growth_rate=db_d.growth_rate,
                    aggression=db_d.aggression, risk_taking=db_d.risk_taking,
                    pressure_handling=db_d.pressure_handling,
                ),
                personality=Personality(db_d.personality),
                slot=DriverSlot(db_d.slot) if db_d.slot else None,
                morale=db_d.morale,
                wins=db_d.wins, podiums=db_d.podiums,
                races_driven=db_d.races_driven,
                is_academy=db_d.is_academy,
            )
            if db_d.slot == 1:
                team.main_driver_1 = d
            elif db_d.slot == 2:
                team.main_driver_2 = d
            elif db_d.slot == 3:
                team.reserve_driver = d

        return team


# ─── Upgrade Views ──────────────────────────────────────────────────────────


class UpgradeSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], team_id: str,
                 user_id: int, session_maker):
        super().__init__(placeholder="🔧 Upgrade auswählen...",
                        options=options, min_values=1, max_values=1)
        self.team_id = team_id
        self.user_id = user_id
        self.session_maker = session_maker

    async def callback(self, interaction: discord.Interaction):
        upgrade_type = self.values[0]
        # Check if it's already max level (has ✅ prefix)
        for opt in self.options:
            if opt.value == upgrade_type and "MAX" in opt.label:
                await interaction.response.send_message(
                    "✅ Dieses Upgrade ist bereits auf Maximallevel!", ephemeral=True)
                return

        # Get current level from DB
        async with self.session_maker() as session:
            result = await session.execute(
                select(TeamUpgradeModel).where(
                    TeamUpgradeModel.team_id == self.team_id,
                    TeamUpgradeModel.upgrade_type == upgrade_type,
                )
            )
            existing = result.scalar_one_or_none()
            current_level = existing.level if existing else 0

        ut = UpgradeType(upgrade_type)
        costs = UPGRADE_COSTS.get(ut, [])
        if current_level >= len(costs):
            await interaction.response.send_message("✅ Max Level erreicht!", ephemeral=True)
            return

        cost = costs[current_level]
        next_level = current_level + 1

        # Show confirm
        confirm_view = UpgradeConfirmView(upgrade_type, next_level, cost,
                                         self.team_id, self.user_id, self.session_maker)
        embed = discord.Embed(
            title=f"🔧 {upgrade_type.title()} → Lv.{next_level}",
            colour=0xFFAA00,
            description=f"Kosten: **${cost:,}**\nBestätigen?",
        )
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)


class UpgradeSelectView(discord.ui.View):
    def __init__(self, options: list[discord.SelectOption], team_id: str,
                 user_id: int, session_maker):
        super().__init__(timeout=120)
        self.add_item(UpgradeSelect(options, team_id, user_id, session_maker))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = self.children[0].user_id
        if user_id is not None and interaction.user.id != user_id:
            await interaction.response.send_message("❌ Nicht dein Menü!", ephemeral=True)
            return False
        return True


class UpgradeConfirmView(discord.ui.View):
    def __init__(self, upgrade_type: str, new_level: int, cost: int,
                 team_id: str, user_id: int, session_maker):
        super().__init__(timeout=60)
        self.upgrade_type = upgrade_type
        self.new_level = new_level
        self.cost = cost
        self.team_id = team_id
        self.user_id = user_id
        self.session_maker = session_maker

    @discord.ui.button(label="✅ Kaufen", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.session_maker() as session:
            from motorsport.data.repository import TeamRepo
            team = await TeamRepo.get(session, self.team_id)
            if not team:
                await interaction.response.edit_message(
                    content="❌ Team nicht gefunden!", embed=None, view=None)
                return

            # Check budget
            if team.budget < self.cost:
                await interaction.response.edit_message(
                    content=f"❌ Nicht genug Budget! Benötigt: ${self.cost:,}, "
                           f"hast: ${float(team.budget):,.0f}",
                    embed=None, view=None)
                return

            # Deduct budget
            team.budget -= self.cost

            # Upsert upgrade
            result = await session.execute(
                select(TeamUpgradeModel).where(
                    TeamUpgradeModel.team_id == self.team_id,
                    TeamUpgradeModel.upgrade_type == self.upgrade_type,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.level = self.new_level
            else:
                import uuid
                new_upgrade = TeamUpgradeModel(
                    id=str(uuid.uuid4()),
                    team_id=self.team_id,
                    upgrade_type=self.upgrade_type,
                    level=self.new_level,
                )
                session.add(new_upgrade)

            session.add(team)
            await session.commit()

        embed = discord.Embed(
            title=f"✅ {self.upgrade_type.title()} auf Lv.{self.new_level}",
            colour=0x00FF00,
            description=f"Kosten: ${self.cost:,}\n"
                       f"Verbleibendes Budget: ${float(team.budget):,.0f}",
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="⏹️ Upgrade abgebrochen", embed=None, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id is not None and interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Nicht dein Menü!", ephemeral=True)
            return False
        return True
