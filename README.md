# EcoTales V2 Lab Project

EcoTales V2 is an educational web app based on my original site. It serves stored eco materials (texts and checklist images) by topic, language, and content type.

## Features

- Existing EcoTales frontend preserved in `frontend/`
- FastAPI backend in `backend/`
- SQLite database in `data/ecotales.db`
- Deterministic materials API
- Material selector by:
  - topic
  - language (`ru`, `en`)
  - content type (`text`, `checklist`)
- Request history saved and shown in UI
- Dockerized and VM-ready structure

## API

- `GET /api/health`
- `POST /api/material`
- `GET /api/history`

### `POST /api/material` body

```json
{
  "topic": "recycling",
  "language": "ru",
  "content_type": "text"
}
```

Response includes resolved material in `result_value`:

- for `text`: text content
- for `checklist`: image path (for example `/images/3_англ.png`)

## Project structure

- `frontend/` static website and assets
- `backend/` FastAPI service
- `data/` SQLite DB file (auto-created)
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`

## Environment variables

Create `.env` from `.env.example`:

- `SQLITE_DB_PATH` default: `data/ecotales.db`

## Run locally

```bash
cd /Users/amelia/Desktop/Лицей/EcoTales/EcoTales_WebSite
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- `http://127.0.0.1:8000`

## Quick API tests

```bash
curl http://127.0.0.1:8000/api/health
```

```bash
curl -X POST http://127.0.0.1:8000/api/material \
  -H "Content-Type: application/json" \
  -d '{"topic":"water_pollution","language":"ru","content_type":"text"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/material \
  -H "Content-Type: application/json" \
  -d '{"topic":"recycling","language":"en","content_type":"checklist"}'
```

```bash
curl http://127.0.0.1:8000/api/history
```

## Docker run

```bash
cd /Users/amelia/Desktop/Лицей/EcoTales/EcoTales_WebSite
cp .env.example .env

docker compose build
docker compose up -d
```

Open:

- `http://127.0.0.1:8000`

Logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

## Ubuntu VM deployment notes

1. Install Docker + Docker Compose plugin.
2. Copy the project to VM.
3. Create `.env` from `.env.example`.
4. Run:

```bash
docker compose build
docker compose up -d
```

5. Open VM firewall port `8000` (or place Nginx in front for 80/443).

The `data/` volume is mounted in compose, so request history persists.
