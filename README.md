# Discord Motorsport Universe

Skalierbares Multiplayer-Motorsport-Management-System für Discord.

## Systemanforderungen

- Python 3.11+
- Docker (optional, für Container-Deployment)

## Schnellstart (Lokal)

```bash
# 1. Python-Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Discord Bot Token setzen (als Umgebungsvariable oder .env)
export DISCORD_TOKEN="dein_token_hier"
export GUILD_ID="deine_guild_id"  # Optional, für schnelleres Slash-Sync

# 3. Bot starten
cd src && python -m bot.main
```

## Deployment mit Docker

```bash
# 1. Docker Compose starten
DISCORD_TOKEN="dein_token" docker compose up -d

# 2. Logs anzeigen
docker compose logs -f

# 3. Stoppen
docker compose down
```

## Deployment auf kostenlosen Servern

### Railway.app (empfohlen)
1. Forke das Repo auf GitHub
2. Gehe zu [Railway.app](https://railway.app)
3. "New Project" → "Deploy from GitHub repo"
4. Setze Environment Variables:
   - `DISCORD_TOKEN`: Dein Bot-Token
   - `GUILD_ID`: (Optional)
5. Railway deployed automatisch — kostenloser Starter-Plan inkl. PostgreSQL

### Fly.io
```bash
flyctl launch
flyctl secrets set DISCORD_TOKEN="dein_token"
flyctl deploy
```

### Render
1. Erstelle einen "Web Service" auf [Render](https://render.com)
2. Verbinde dein GitHub-Repo
3. Setze `Start Command` auf `python -m bot.main`
4. Füge `DISCORD_TOKEN` als Secret hinzu

## Discord Bot Setup

1. Gehe zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Erstelle eine neue Application
3. Gehe zu "Bot" → "Add Bot"
4. Kopiere den Token
5. Aktiviere diese Privileged Gateway Intents:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
6. Gehe zu "OAuth2" → "URL Generator"
7. Wähle Scopes: `bot` + `applications.commands`
8. Wähle Permissions: `Send Messages` + `Embed Links` + `Use Slash Commands`
9. Lade den Bot mit dem generierten Link in deinen Server ein

## Projektstruktur

```
discord-motorsport-universe/
├── src/motorsport/       # Game Engine
│   ├── models/           # Data models (dataclasses)
│   ├── simulation/       # Engine, name/driver gen, ranking
│   ├── systems/          # Sponsors, academy, events, season
│   └── data/             # SQLAlchemy DB layer
├── bot/                  # Discord Bot
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── embeds.py         # Embed builders
│   └── cogs/             # Command cogs
├── tests/                # Integration tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Commands

| Command | Beschreibung |
|---------|-------------|
| `/help` | Alle Befehle anzeigen |
| `/team` | Team-Übersicht |
| `/team_create` | Team erstellen |
| `/drivers` | Fahrer-Liste |
| `/driver` | Fahrer-Details |
| `/race` | Rennen simulieren |
| `/qualifier` | Qualifier-Übersicht |
| `/qualifier_run` | Qualifier fahren |
| `/season` | Saison-Status |
| `/market` | Transfermarkt |
| `/train` | Training |
| `/sponsor` | Sponsoren |
| `/academy` | Academy |
| `/league` | Ligen-Info |
| `/premium` | Premium-Infos |
