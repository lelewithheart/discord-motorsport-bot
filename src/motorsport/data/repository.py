"""
Repository layer — CRUD operations for all game entities.
Provides async methods to save/load/query game state from the database.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from motorsport.data.models import (
    PlayerModel, TeamModel, DriverModel, SponsorModel, TeamUpgradeModel,
    QualifierModel, RaceResultModel, SeasonRankingModel, WorldEventModel,
    TransferModel, ScoutModel,
)


class PlayerRepo:
    @staticmethod
    async def get_or_create(session: AsyncSession, discord_id: int,
                             username: str) -> PlayerModel:
        result = await session.execute(
            select(PlayerModel).where(PlayerModel.id == discord_id)
        )
        player = result.scalar_one_or_none()
        if player is None:
            player = PlayerModel(id=discord_id, username=username)
            session.add(player)
            await session.commit()
        return player

    @staticmethod
    async def get(session: AsyncSession, discord_id: int) -> Optional[PlayerModel]:
        result = await session.execute(
            select(PlayerModel).where(PlayerModel.id == discord_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set_premium(session: AsyncSession, discord_id: int,
                          premium: bool = True):
        player = await PlayerRepo.get(session, discord_id)
        if player:
            player.is_premium = premium
            await session.commit()


class TeamRepo:
    @staticmethod
    async def create(session: AsyncSession, owner_id: int,
                     name: str, league: int = 10) -> TeamModel:
        team = TeamModel(owner_id=owner_id, name=name, league=league)
        session.add(team)
        await session.commit()
        return team

    @staticmethod
    async def get(session: AsyncSession, team_id: str) -> Optional[TeamModel]:
        result = await session.execute(
            select(TeamModel).where(TeamModel.id == team_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_owner(session: AsyncSession, owner_id: int) -> list[TeamModel]:
        result = await session.execute(
            select(TeamModel).where(TeamModel.owner_id == owner_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_league(session: AsyncSession, league: int) -> list[TeamModel]:
        result = await session.execute(
            select(TeamModel).where(TeamModel.league == league)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(session: AsyncSession, team: TeamModel):
        session.add(team)
        await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, team_id: str):
        await session.execute(
            delete(TeamModel).where(TeamModel.id == team_id)
        )
        await session.commit()


class DriverRepo:
    @staticmethod
    async def create(session: AsyncSession, driver_data: dict) -> DriverModel:
        driver = DriverModel(**driver_data)
        session.add(driver)
        await session.commit()
        return driver

    @staticmethod
    async def create_many(session: AsyncSession, drivers: list[dict]) -> list[DriverModel]:
        models = [DriverModel(**d) for d in drivers]
        session.add_all(models)
        await session.commit()
        return models

    @staticmethod
    async def get(session: AsyncSession, driver_id: str) -> Optional[DriverModel]:
        result = await session.execute(
            select(DriverModel).where(DriverModel.id == driver_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_team(session: AsyncSession, team_id: str) -> list[DriverModel]:
        result = await session.execute(
            select(DriverModel).where(DriverModel.team_id == team_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_free_agents(session: AsyncSession) -> list[DriverModel]:
        """Drivers without a team (for transfer market)."""
        result = await session.execute(
            select(DriverModel).where(
                DriverModel.team_id.is_(None),
                DriverModel.is_retired == False
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(session: AsyncSession, driver: DriverModel):
        session.add(driver)
        await session.commit()

    @staticmethod
    async def retire_driver(session: AsyncSession, driver_id: str,
                             season: int):
        driver = await DriverRepo.get(session, driver_id)
        if driver:
            driver.is_retired = True
            driver.retirement_season = season
            driver.team_id = None
            await session.commit()


class QualifierRepo:
    @staticmethod
    async def save(session: AsyncSession, qualifier: QualifierModel):
        session.add(qualifier)
        await session.commit()

    @staticmethod
    async def get_by_season(session: AsyncSession, league: int,
                             season: int) -> list[QualifierModel]:
        result = await session.execute(
            select(QualifierModel).where(
                QualifierModel.league == league,
                QualifierModel.season == season,
            ).order_by(QualifierModel.race_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_league_median(session: AsyncSession, league: int,
                                 season: int, race_number: int) -> int:
        """Calculate median qualifier time for a league."""
        result = await session.execute(
            select(QualifierModel.average_time_ms).where(
                QualifierModel.league == league,
                QualifierModel.season == season,
                QualifierModel.race_number == race_number,
            )
        )
        times = sorted(result.scalars().all())
        if not times:
            return 90000  # default 90s
        n = len(times)
        if n % 2 == 0:
            return (times[n // 2 - 1] + times[n // 2]) // 2
        return times[n // 2]


class RankingRepo:
    @staticmethod
    async def save_all(session: AsyncSession, rankings: list[SeasonRankingModel]):
        session.add_all(rankings)
        await session.commit()

    @staticmethod
    async def get_by_league(session: AsyncSession, league: int,
                             season: int) -> list[SeasonRankingModel]:
        result = await session.execute(
            select(SeasonRankingModel).where(
                SeasonRankingModel.league == league,
                SeasonRankingModel.season == season,
            ).order_by(SeasonRankingModel.rank)
        )
        return list(result.scalars().all())
