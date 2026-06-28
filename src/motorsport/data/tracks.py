"""Track definitions with stat requirements."""
from __future__ import annotations

TRACK_LIST = [
    {"name": "Monaco", "country": "Monaco", "req_speed": 0.3, "req_acceleration": 0.6, "req_downforce": 0.9, "req_braking": 0.8, "req_tyre_management": 0.5, "lap_length_km": 3.3},
    {"name": "Monza", "country": "Italy", "req_speed": 0.9, "req_acceleration": 0.5, "req_downforce": 0.2, "req_braking": 0.4, "req_tyre_management": 0.6, "lap_length_km": 5.8},
    {"name": "Silverstone", "country": "UK", "req_speed": 0.7, "req_acceleration": 0.6, "req_downforce": 0.6, "req_braking": 0.5, "req_tyre_management": 0.7, "lap_length_km": 5.9},
    {"name": "Spa", "country": "Belgium", "req_speed": 0.8, "req_acceleration": 0.5, "req_downforce": 0.5, "req_braking": 0.6, "req_tyre_management": 0.6, "lap_length_km": 7.0},
    {"name": "Suzuka", "country": "Japan", "req_speed": 0.6, "req_acceleration": 0.5, "req_downforce": 0.7, "req_braking": 0.5, "req_tyre_management": 0.8, "lap_length_km": 5.8},
    {"name": "Interlagos", "country": "Brazil", "req_speed": 0.7, "req_acceleration": 0.7, "req_downforce": 0.4, "req_braking": 0.6, "req_tyre_management": 0.5, "lap_length_km": 4.3},
    {"name": "Red Bull Ring", "country": "Austria", "req_speed": 0.7, "req_acceleration": 0.8, "req_downforce": 0.3, "req_braking": 0.6, "req_tyre_management": 0.3, "lap_length_km": 4.3},
    {"name": "Hungaroring", "country": "Hungary", "req_speed": 0.4, "req_acceleration": 0.5, "req_downforce": 0.8, "req_braking": 0.7, "req_tyre_management": 0.6, "lap_length_km": 4.4},
    {"name": "Baku", "country": "Azerbaijan", "req_speed": 0.8, "req_acceleration": 0.4, "req_downforce": 0.3, "req_braking": 0.7, "req_tyre_management": 0.4, "lap_length_km": 6.0},
    {"name": "Zandvoort", "country": "Netherlands", "req_speed": 0.5, "req_acceleration": 0.6, "req_downforce": 0.8, "req_braking": 0.6, "req_tyre_management": 0.5, "lap_length_km": 4.3},
    {"name": "Shanghai", "country": "China", "req_speed": 0.7, "req_acceleration": 0.5, "req_downforce": 0.6, "req_braking": 0.5, "req_tyre_management": 0.7, "lap_length_km": 5.5},
    {"name": "Yas Marina", "country": "UAE", "req_speed": 0.6, "req_acceleration": 0.4, "req_downforce": 0.5, "req_braking": 0.4, "req_tyre_management": 0.8, "lap_length_km": 5.6},
    {"name": "Melbourne", "country": "Australia", "req_speed": 0.5, "req_acceleration": 0.6, "req_downforce": 0.6, "req_braking": 0.7, "req_tyre_management": 0.5, "lap_length_km": 5.3},
    {"name": "Imola", "country": "Italy", "req_speed": 0.5, "req_acceleration": 0.5, "req_downforce": 0.7, "req_braking": 0.6, "req_tyre_management": 0.6, "lap_length_km": 4.9},
]


async def seed_tracks(session):
    """Insert tracks into DB if empty."""
    from sqlalchemy import select
    from motorsport.data.models import TrackModel

    result = await session.execute(select(TrackModel).limit(1))
    if result.scalar_one_or_none() is None:
        for t in TRACK_LIST:
            import uuid
            session.add(TrackModel(id=str(uuid.uuid4()), **t))
        await session.commit()
