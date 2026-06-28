# Motorsport Universe V2 — Daily Racing + Training + Setup + R&D

> **For Hermes:** Implement task-by-task using subagent-driven-development.

**Goal:** Redesign the Motorsport Discord Bot with daily races at 20:00 CEST, training laps, car setups, R&D system, track-specific stats, 14-race seasons, and off-season.

**Architecture:**
- **Scheduler** — `APScheduler` in background thread triggers `/race` at 20:00 daily
- **Training** — 20 laps/day, split between drivers, each lap earns R&D points
- **Setup** — Save/load car configs per track (Front Wing, Rear Wing, Suspension, Gearing, Tires)
- **R&D** — Points from laps, upgrade components (Engine, Aero, Chassis, etc.)
- **Track Stats** — Each track has 3 primary stat requirements (e.g. Speed/Accel/Downforce)
- **Off-Season** — 7 days, 80 R&D laps/day, scouting, upgrades
- **Replace** old upgrade system with new R&D-based system

**Tech Stack:** Python 3.11, discord.py, SQLAlchemy async, APScheduler

---

## Phase 1 — Data Layer

### Task 1: New SQLAlchemy Models

**Models needed:**

```python
class TrackModel(Base):
    __tablename__ = "tracks"
    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(64), nullable=False, unique=True)
    country = Column(String(64))
    # Stat requirements (0.0-1.0 multiplier for each stat)
    req_speed = Column(Float, default=0.5)       # How much speed matters
    req_acceleration = Column(Float, default=0.5)
    req_downforce = Column(Float, default=0.5)    # Cornering
    req_braking = Column(Float, default=0.5)
    req_tyre_management = Column(Float, default=0.5)
    lap_length_km = Column(Float, default=5.0)   # For fuel simulation


class SetupModel(Base):
    __tablename__ = "setups"
    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=True)  # None = default
    name = Column(String(64), default="Default")
    # Setup parameters (1-20 scale)
    front_wing = Column(Integer, default=10)       # 1=low downforce, 20=high downforce
    rear_wing = Column(Integer, default=10)
    suspension = Column(Integer, default=10)        # 1=soft, 20=hard
    gear_ratio = Column(Integer, default=10)        # 1=short (accel), 20=long (top speed)
    tire_compound = Column(Integer, default=10)     # 1=soft (grip), 20=hard (durability)
    is_default = Column(Boolean, default=False)


class TrainingSessionModel(Base):
    __tablename__ = "training_sessions"
    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)
    lap_count = Column(Integer, default=0)          # How many laps run
    best_lap_ms = Column(Integer, nullable=True)
    avg_lap_ms = Column(Integer, nullable=True)
    setup_id = Column(String(36), ForeignKey("setups.id"), nullable=True)
    session_date = Column(DateTime, default=datetime.utcnow)


class RndUpgradeModel(Base):
    __tablename__ = "rnd_upgrades"
    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    component = Column(String(32), nullable=False)  # 'engine', 'front_wing', 'rear_wing', 'chassis', 'brakes', 'gearbox'
    level = Column(Integer, default=1)
    rnd_spent = Column(Integer, default=0)          # Total R&D points spent on this


class RndPointsModel(Base):
    __tablename__ = "rnd_points"
    id = Column(String(36), primary_key=True, default=_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    season = Column(Integer, nullable=False)
    points = Column(Integer, default=0)


class RaceScheduleModel(Base):
    __tablename__ = "race_schedule"
    id = Column(String(36), primary_key=True, default=_uuid)
    league = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    race_number = Column(Integer, nullable=False)
    track_id = Column(String(36), ForeignKey("tracks.id"), nullable=False)
    race_date = Column(Date, nullable=False)         # The day the race runs
    qualifier_deadline = Column(DateTime, nullable=True)  # 19:30 on race day
    is_completed = Column(Boolean, default=False)
```

**Files:**
- Modify: `src/motorsport/data/models.py` — Add all new models above
- Modify: `src/motorsport/data/__init__.py` — Export new models
- Create: `src/motorsport/data/tracks.py` — Track data with all tracks and stat reqs

### Task 2: New Repository Methods

- `SetupRepo` — create, get_by_team, get_by_track, update, delete
- `TrainingRepo` — create, get_by_team_race, update
- `RndRepo` — get_points, add_points, get_upgrades, upgrade_component
- `TrackRepo` — get_all, get_by_name/search
- `RaceScheduleRepo` — get_today_race, get_by_league_season, mark_complete
- `TeamModel` — add fields: `rnd_multiplier` (for upgrades affecting R&D gain)

**Files:**
- Modify: `src/motorsport/data/repository.py`

### Task 3: Track Data

**File:** `src/motorsport/data/tracks.py`

14 tracks with realistic names and stat requirements:
```python
TRACKS = [
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
```

---

## Phase 2 — Game Systems

### Task 4: Training System

**File:** `src/motorsport/systems/training.py`

```python
class TrainingEngine:
    """
    Simulates training laps for a driver.
    Each lap:
    1. Takes driver stats + setup + track requirements
    2. Calculates lap time based on these factors
    3. Applies R&D points earned (1 point per lap, multiplied by upgrades)
    4. Returns individual lap times and average
    """
    
    RND_POINTS_PER_LAP = 1
    MAX_TRAINING_LAPS = 20  # Per day, shared between drivers
    
    def simulate_lap(self, driver, setup, track, weather) -> int:
        """Simulate one lap, return time in ms."""
        pass
    
    def run_training(self, team, driver, setup, track, laps: int, weather) -> dict:
        """Run N training laps for a driver."""
        pass
    
    def get_best_setup(self, driver, track) -> dict:
        """Return the theoretical best setup for this driver/track combo."""
        pass
```

### Task 5: Setup System

**File:** `src/motorsport/systems/setup.py`

```python
class SetupCalculator:
    """
    Calculates how a given setup affects a driver's performance on a specific track.
    
    Setup parameters (each 1-20):
    - Front Wing: Affects downforce (cornering) vs speed
    - Rear Wing: Affects rear stability vs speed  
    - Suspension: Affects tire wear vs responsiveness
    - Gear Ratio: Short = accel, Long = top speed
    - Tire Compound: Soft = grip (fast), Hard = durability
    
    Each driver has hidden preferences:
    - Preferred wing balance (understeer vs oversteer)
    - Preferred suspension stiffness
    """
    
    def calculate_setup_bonus(self, setup, driver, track) -> dict:
        """Return a dict of stat multipliers from this setup."""
        pass
    
    def calculate_driver_happiness(self, setup, driver) -> float:
        """0.0-1.0 How much the driver likes this setup."""
        pass
    
    def optimize_for_track(self, track) -> dict:
        """Return recommended setup ranges for this track."""
        pass
```

### Task 6: R&D System

**File:** `src/motorsport/systems/rnd.py`

```python
RND_COMPONENTS = {
    "engine": {
        "name": "Motor",
        "max_level": 10,
        "costs": [100, 250, 500, 800, 1200, 1700, 2300, 3000, 4000, 5000],
        "effects": {"speed": 2, "acceleration": 1},
    },
    "front_wing": {
        "name": "Frontflügel",
        "max_level": 10,
        "costs": [80, 200, 400, 650, 950, 1300, 1800, 2400, 3200, 4000],
        "effects": {"downforce": 3, "speed": -0.5},
    },
    "rear_wing": {
        "name": "Heckflügel",
        "max_level": 10,
        "costs": [80, 200, 400, 650, 950, 1300, 1800, 2400, 3200, 4000],
        "effects": {"downforce": 2, "stability": 3},
    },
    "chassis": {
        "name": "Chassis",
        "max_level": 10,
        "costs": [120, 300, 550, 900, 1300, 1800, 2500, 3200, 4200, 5500],
        "effects": {"braking": 2, "tyre_management": 1, "speed": 1},
    },
    "brakes": {
        "name": "Bremsen",
        "max_level": 8,
        "costs": [60, 150, 300, 500, 750, 1000, 1400, 1800],
        "effects": {"braking": 4},
    },
    "gearbox": {
        "name": "Getriebe",
        "max_level": 8,
        "costs": [70, 180, 350, 550, 800, 1100, 1500, 2000],
        "effects": {"acceleration": 3, "speed": 1},
    },
}

class RndManager:
    def add_points(self, team_id, season, laps):
        """Add R&D points for completed laps."""
        pass
    
    def get_upgrade_cost(self, component, current_level):
        """Get R&D points needed for next level."""
        pass
    
    def apply_upgrade_effects(self, team, driver):
        """Apply R&D upgrade bonuses to driver/team stats."""
        pass
```

### Task 7: Modified Race Engine

- Modify `SimulationEngine.simulate_race` to use:
  - Driver stats × track requirements × setup bonuses
  - R&D level bonuses
  - Current setup configuration
- Qualifier fallback: if no qualifier run, position from ranking

**Files:**
- Modify: `src/motorsport/simulation/engine.py`

### Task 8: Scheduler (Daily 20:00 Race)

**File:** `bot/scheduler.py`

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def run_daily_race(bot):
    """Called at 20:00 daily. Runs races for all leagues."""
    # 1. Check qualifier deadline (19:30) - apply fallback positions
    # 2. Simulate all races
    # 3. Post results to configured channel
    # 4. Update season state
    pass

def start_scheduler(bot):
    """Start the daily race scheduler."""
    scheduler.add_job(
        run_daily_race,
        trigger='cron',
        hour=20,
        minute=0,
        timezone='Europe/Vienna',
        args=[bot],
        id='daily_race',
        replace_existing=True,
    )
    scheduler.start()
```

**Modify:**
- `bot/main.py` — Start scheduler after bot connects

### Task 9: Season System update

- Change `RACES_PER_SEASON` from 12 to 14
- Add off-season logic (7 days, 80 R&D laps/day)
- Track week progression with dates

**Files:**
- Modify: `bot/config.py` — Change default
- Modify: `src/motorsport/systems/season.py`

---

## Phase 3 — Discord Cogs

### Task 10: Setup Cog

**File:** `bot/cogs/setup_cog.py`

Commands:
- `/setup` — Show current setup for this track
- `/setup adjust <param> <value>` — Adjust a setup parameter (1-20)
- `/setup save <name>` — Save current setup
- `/setup load <name>` — Load saved setup
- `/setup list` — List saved setups
- `/setup default <name>` — Set as default
- `/setup recommend` — Show recommended setup for current track

### Task 11: Training Cog

**File:** `bot/cogs/training_cog.py`

Commands:
- `/train <driver_id> <laps>` — Run training laps for a driver
- `/training status` — Show remaining laps today + results
- `/training history` — Show training log

### Task 12: R&D Cog

**File:** `bot/cogs/rnd_cog.py`

Commands:
- `/rnd` — Show R&D overview (points, upgrades)
- `/rnd upgrade <component>` — Upgrade a component
- `/rnd tree` — Show tech tree with costs and effects

### Task 13: Qualifying Cog (updated)

**File:** `bot/cogs/qualifier.py` (modify)

Updated qualifying:
- `/qualifier run` — Run hotlap for starting position
- Uses current setup if available
- If not run by 19:30, starting position from ranking

### Task 14: Race Schedule Cog

**File:** `bot/cogs/season_cog.py` (modify)

Commands:
- `/schedule` — Show upcoming races
- `/season` — Updated for 14 races

### Task 15: Dashboard Cog

**File:** `bot/cogs/dashboard_cog.py`

Commands:
- `/dashboard` — Big overview with: current race countdown, R&D points, training status, setup, next race info

---

## Files Changed Summary

| Action | File |
|---|---|
| Create | `src/motorsport/data/tracks.py` |
| Create | `src/motorsport/systems/training.py` |
| Create | `src/motorsport/systems/setup.py` |
| Create | `src/motorsport/systems/rnd.py` |
| Create | `bot/scheduler.py` |
| Create | `bot/cogs/setup_cog.py` |
| Create | `bot/cogs/training_cog.py` |
| Create | `bot/cogs/rnd_cog.py` |
| Create | `bot/cogs/dashboard_cog.py` |
| Modify | `src/motorsport/data/models.py` |
| Modify | `src/motorsport/data/__init__.py` |
| Modify | `src/motorsport/data/repository.py` |
| Modify | `src/motorsport/simulation/engine.py` |
| Modify | `src/motorsport/systems/season.py` |
| Modify | `bot/config.py` |
| Modify | `bot/main.py` |
| Modify | `bot/cogs/qualifier.py` |
| Modify | `bot/cogs/__init__.py` |

---

## Execution Order

1. Track data + DB models
2. Repository methods  
3. Setup system
4. Training system
5. R&D system
6. Modified race engine
7. Scheduler
8. Setup Cog
9. Training Cog
10. R&D Cog
11. Dashboard Cog
12. Update existing cogs (qualifier, season)
13. Build & Deploy
