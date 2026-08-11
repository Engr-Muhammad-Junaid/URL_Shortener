# URL Shortener API

A production-ready URL shortener built with FastAPI.

## Tech Stack
- FastAPI + SQLAlchemy + PostgreSQL
- Alembic (migrations)
- Docker + docker-compose
- pytest (testing)
- GitHub Actions (CI/CD)
- Loguru (logging)
- SlowAPI (rate limiting)

## Getting Started

### With Docker (recommended)
docker-compose up --build
docker-compose exec app alembic upgrade head

### Local Development
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set ADMIN_PASSWORD and SESSION_SECRET in .env before starting
alembic upgrade head
uvicorn app.main:app --reload

## API Endpoints
| Method | Endpoint       | Description         | Rate Limit   |
|--------|----------------|---------------------|--------------|
| POST   | /urls          | Create short URL    | 10/minute    |
| GET    | /{short_code}  | Redirect to URL     | 30/minute    |
| GET    | /urls/all      | List all URLs       | 30/minute    |
| DELETE | /urls/{id}     | Delete a URL        | 10/minute    |
| GET    | /health        | Health check        | Unlimited    |

## Running Tests
pytest tests/ -v

## Docs
http://localhost:8000/docs

## Web interface
Start the API, then open http://localhost:8000 in your browser. This is the
public page where visitors can create and copy a short link. The owner workspace
with link history, click counts, and delete controls is available separately at
http://localhost:8000/dashboard. The dashboard, URL list API, and delete API all
require an authenticated owner session. Sign in with the `ADMIN_PASSWORD` from
your `.env` file. Generate a production signing secret with
`openssl rand -hex 32` and store it as `SESSION_SECRET`.

## Deploying to Render with Neon

This repository includes a `render.yaml` Blueprint and Docker configuration.
Create a Neon project, copy its pooled PostgreSQL connection string, and keep
`sslmode=require` in the URL. In Render, create a Blueprint from this GitHub
repository and enter these secret environment values when prompted:

- `DATABASE_URL`: the Neon pooled connection string
- `ADMIN_PASSWORD`: a unique, strong dashboard password

Render generates `SESSION_SECRET`, runs Alembic migrations during container
startup, checks `/health`, and deploys the `main` branch only after GitHub CI
passes. Never add `.env`, the Neon URL, or production passwords to GitHub.
