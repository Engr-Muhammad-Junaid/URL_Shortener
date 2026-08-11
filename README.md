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
