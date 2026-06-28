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
    TransferModel, ScoutModel, TrackModel, SetupModel,
    TrainingSessionModel, RndUpgradeModel, RndPointsModel,
    RaceScheduleModel,
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
    async def get_all(session: AsyncSession) -> list[TeamModel]:
        """Get all teams."""
        result = await session.execute(select(TeamModel))
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

    @staticmethod
    async def get_by_team_race(session: AsyncSession, team_id: str,
                                season: int, race_number: int) -> Optional[QualifierModel]:
        """Get qualifier for a specific team, season, and race."""
        result = await session.execute(
            select(QualifierModel).where(
                QualifierModel.team_id == team_id,
                QualifierModel.season == season,
                QualifierModel.race_number == race_number,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_by_race(session: AsyncSession, league: int,
                               season: int, race_number: int) -> list[QualifierModel]:
        """Get all qualifiers for a specific race."""
        result = await session.execute(
            select(QualifierModel).where(
                QualifierModel.league == league,
                QualifierModel.season == season,
                QualifierModel.race_number == race_number,
            )
        )
        return list(result.scalars().all())


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


class TrackRepo:
    @staticmethod
    async def get_all(session: AsyncSession) -> list[TrackModel]:
        result = await session.execute(select(TrackModel).order_by(TrackModel.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[TrackModel]:
        result = await session.execute(select(TrackModel).where(TrackModel.name.ilike(f"%{name}%")))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, track_id: str) -> Optional[TrackModel]:
        result = await session.execute(select(TrackModel).where(TrackModel.id == track_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def seed_if_empty(session: AsyncSession):
        """Seed tracks from tracks.py if empty."""
        result = await session.execute(select(TrackModel).limit(1))
        if result.scalar_one_or_none() is None:
            from motorsport.data.tracks import TRACK_LIST
            import uuid
            for t in TRACK_LIST:
                session.add(TrackModel(id=str(uuid.uuid4()), **t))
            await session.commit()
            return len(TRACK_LIST)
        return 0


class SetupRepo:
    @staticmethod
    async def create(session: AsyncSession, team_id: str, name: str = "Default",
                     track_id: Optional[str] = None, **params) -> SetupModel:
        import uuid
        setup = SetupModel(
            id=str(uuid.uuid4()),
            team_id=team_id,
            name=name,
            track_id=track_id,
            front_wing=params.get("front_wing", 10),
            rear_wing=params.get("rear_wing", 10),
            suspension=params.get("suspension", 10),
            gear_ratio=params.get("gear_ratio", 10),
            tire_compound=params.get("tire_compound", 10),
        )
        session.add(setup)
        await session.commit()
        return setup

    @staticmethod
    async def get_by_team(session: AsyncSession, team_id: str) -> list[SetupModel]:
        result = await session.execute(
            select(SetupModel).where(SetupModel.team_id == team_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_track(session: AsyncSession, team_id: str,
                            track_id: Optional[str] = None) -> list[SetupModel]:
        """Get setups for a specific track. If track_id=None, get defaults."""
        result = await session.execute(
            select(SetupModel).where(
                SetupModel.team_id == team_id,
                SetupModel.track_id == track_id,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_default(session: AsyncSession, team_id: str) -> Optional[SetupModel]:
        result = await session.execute(
            select(SetupModel).where(
                SetupModel.team_id == team_id,
                SetupModel.is_default == True,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get(session: AsyncSession, setup_id: str) -> Optional[SetupModel]:
        result = await session.execute(select(SetupModel).where(SetupModel.id == setup_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(session: AsyncSession, setup: SetupModel):
        session.add(setup)
        await session.commit()

    @staticmethod
    async def set_default(session: AsyncSession, team_id: str, setup_id: str):
        """Set one setup as default, unset others."""
        result = await session.execute(
            select(SetupModel).where(SetupModel.team_id == team_id)
        )
        all_setups = list(result.scalars().all())
        for s in all_setups:
            s.is_default = (s.id == setup_id)
        await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, setup_id: str):
        await session.execute(delete(SetupModel).where(SetupModel.id == setup_id))
        await session.commit()


class TrainingRepo:
    @staticmethod
    async def get_or_create(session: AsyncSession, team_id: str, driver_id: str,
                             track_id: str, season: int, race_number: int) -> TrainingSessionModel:
        result = await session.execute(
            select(TrainingSessionModel).where(
                TrainingSessionModel.team_id == team_id,
                TrainingSessionModel.driver_id == driver_id,
                TrainingSessionModel.season == season,
                TrainingSessionModel.race_number == race_number,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        import uuid
        session_obj = TrainingSessionModel(
            id=str(uuid.uuid4()),
            team_id=team_id,
            driver_id=driver_id,
            track_id=track_id,
            season=season,
            race_number=race_number,
        )
        session.add(session_obj)
        await session.commit()
        return session_obj

    @staticmethod
    async def get_by_team_race(session: AsyncSession, team_id: str,
                                 season: int, race_number: int) -> list[TrainingSessionModel]:
        result = await session.execute(
            select(TrainingSessionModel).where(
                TrainingSessionModel.team_id == team_id,
                TrainingSessionModel.season == season,
                TrainingSessionModel.race_number == race_number,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(session: AsyncSession, training: TrainingSessionModel):
        session.add(training)
        await session.commit()


class RndRepo:
    @staticmethod
    async def get_points(session: AsyncSession, team_id: str,
                          season: int) -> RndPointsModel:
        result = await session.execute(
            select(RndPointsModel).where(
                RndPointsModel.team_id == team_id,
                RndPointsModel.season == season,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        import uuid
        rp = RndPointsModel(id=str(uuid.uuid4()), team_id=team_id, season=season)
        session.add(rp)
        await session.commit()
        return rp

    @staticmethod
    async def add_points(session: AsyncSession, team_id: str,
                          season: int, points: int):
        rp = await RndRepo.get_points(session, team_id, season)
        rp.points += points
        await session.commit()
        return rp.points

    @staticmethod
    async def get_upgrades(session: AsyncSession, team_id: str) -> list[RndUpgradeModel]:
        result = await session.execute(
            select(RndUpgradeModel).where(RndUpgradeModel.team_id == team_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_upgrade(session: AsyncSession, team_id: str,
                           component: str) -> Optional[RndUpgradeModel]:
        result = await session.execute(
            select(RndUpgradeModel).where(
                RndUpgradeModel.team_id == team_id,
                RndUpgradeModel.component == component,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upgrade_component(session: AsyncSession, team_id: str,
                                 component: str, cost: int) -> RndUpgradeModel:
        """Upgrade a component. Creates if not exists."""
        existing = await RndRepo.get_upgrade(session, team_id, component)
        if existing:
            existing.level += 1
        else:
            import uuid
            existing = RndUpgradeModel(
                id=str(uuid.uuid4()),
                team_id=team_id,
                component=component,
                level=2,  # Starting at level 1, first upgrade = 2
            )
            session.add(existing)
        await session.commit()
        return existing


class RaceScheduleRepo:
    @staticmethod
    async def get_today_race(session: AsyncSession) -> Optional[RaceScheduleModel]:
        """Get today's race."""
        from datetime import date
        result = await session.execute(
            select(RaceScheduleModel).where(
                RaceScheduleModel.race_date == date.today(),
                RaceScheduleModel.is_completed == False,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[RaceScheduleModel]:
        """Get all schedule entries ordered by race_number."""
        result = await session.execute(
            select(RaceScheduleModel).order_by(RaceScheduleModel.race_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_season(session: AsyncSession, season: int) -> list[RaceScheduleModel]:
        """Get schedule for a specific season."""
        result = await session.execute(
            select(RaceScheduleModel).where(
                RaceScheduleModel.season == season,
            ).order_by(RaceScheduleModel.race_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_upcoming(session: AsyncSession) -> list[RaceScheduleModel]:
        """Get all upcoming (not completed) races."""
        result = await session.execute(
            select(RaceScheduleModel).where(
                RaceScheduleModel.is_completed == False,
            ).order_by(RaceScheduleModel.race_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_completed(session: AsyncSession, race_schedule_id: str):
        """Mark a race as completed."""
        result = await session.execute(
            select(RaceScheduleModel).where(RaceScheduleModel.id == race_schedule_id)
        )
        rs = result.scalar_one_or_none()
        if rs:
            rs.is_completed = True
            await session.commit()

    @staticmethod
    async def generate_schedule(session: AsyncSession, season: int, tracks: list) -> int:
        """Generate 14-race global schedule starting from tomorrow."""
        from datetime import date, timedelta, datetime, time
        import uuid
        start_date = date.today() + timedelta(days=1)
        # Check if schedule already exists for this season
        existing = await RaceScheduleRepo.get_by_season(session, season)
        if existing:
            return 0
        for i, track in enumerate(tracks[:14]):
            race_date = start_date + timedelta(days=i)
            deadline = datetime.combine(race_date, time(19, 30))
            rs = RaceScheduleModel(
                id=str(uuid.uuid4()),
                season=season,
                race_number=i + 1,
                track_id=track.id,
                race_date=race_date,
                qualifier_deadline=deadline,
            )
            session.add(rs)
        await session.commit()
        return min(14, len(tracks))

    @staticmethod
    async def get_current_race(session: AsyncSession) -> Optional[RaceScheduleModel]:
        """Get the current (first incomplete) race."""
        result = await session.execute(
            select(RaceScheduleModel).where(
                RaceScheduleModel.is_completed == False,
            ).order_by(RaceScheduleModel.race_number).limit(1)
        )
        return result.scalar_one_or_none()
