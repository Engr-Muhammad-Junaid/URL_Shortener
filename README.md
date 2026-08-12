# Snip URL Shortener

A full-stack URL shortener built with FastAPI, PostgreSQL, and a responsive
browser interface. Create shareable short links, track clicks, and manage links
from a protected owner dashboard.

## Live application

- **Public shortener:** https://url-shortener-aic-oder.vercel.app
- **Owner login:** https://url-shortener-aic-oder.vercel.app/login
- **Health check:** https://url-shortener-aic-oder.vercel.app/health

The dashboard requires the private production `ADMIN_PASSWORD` and is available
at `/dashboard` after authentication.

## Tech Stack

- FastAPI + SQLAlchemy + PostgreSQL
- Vanilla HTML, CSS, and JavaScript
- Neon PostgreSQL (production)
- Vercel Python runtime (production)
- Alembic (migrations)
- Docker + docker-compose
- pytest (testing)
- GitHub Actions (CI/CD)
- Loguru (logging)
- SlowAPI (rate limiting)

## Getting Started

### With Docker (recommended)

```bash
docker-compose up --build
docker-compose exec app alembic upgrade head
```

### Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set ADMIN_PASSWORD and SESSION_SECRET in .env before starting
alembic upgrade head
uvicorn app.main:app --reload
```

## API Endpoints
| Method | Endpoint       | Description         | Rate Limit   |
|--------|----------------|---------------------|--------------|
| POST   | /urls          | Create short URL    | 10/minute    |
| GET    | /{short_code}  | Redirect to URL     | 30/minute    |
| GET    | /urls/all      | List all URLs       | 30/minute    |
| DELETE | /urls/{id}     | Delete a URL        | 10/minute    |
| GET    | /health        | Health check        | Unlimited    |

## Running Tests

```bash
pytest tests/ -v
```

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

## Deploying to Vercel with Neon

Vercel uses the root `index.py` as one zero-configuration FastAPI function.
Add `DATABASE_URL`, `ADMIN_PASSWORD`,
`SESSION_SECRET`, `DEBUG=false`, and `APP_NAME` to the Vercel project for the
Production environment.

Before the first deployment, add the pooled Neon URL to the GitHub repository
as an Actions secret named `NEON_DATABASE_URL`. Run the **Migrate production
database** workflow manually from the Actions tab. This keeps database
credentials out of source control and applies Alembic migrations before the
application begins receiving requests.

## Environments and CI/CD

Configuration and secrets are intentionally separated:

| Environment | Configuration source | Database |
|---|---|---|
| Local | Ignored `.env` file | Local development PostgreSQL |
| GitHub CI | Test-only workflow values | Temporary PostgreSQL service |
| GitHub migrations | `production` environment secret | Neon production database |
| Vercel | Encrypted project environment variables | Neon production database |

Every push and pull request to `main` runs pytest plus Python and JavaScript
syntax checks. A push to `main` also triggers a Vercel production deployment.
The `.env` file and production credentials must never be committed.

### Normal code changes

Changes that do not modify the database schema need only the normal Git flow:

```bash
pytest -q
git add .
git commit -m "Describe the change"
git push origin main
```

GitHub CI validates the commit and Vercel deploys it automatically.

### Database schema changes

Model changes such as adding, renaming, or removing a column also require an
Alembic migration:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
pytest -q
```

Review the generated migration before committing it. For production, use a
backward-compatible migration first, push it, and run **Migrate production
database** from GitHub Actions. Push application code that requires the new
schema only after the production migration succeeds.

## License

This project is available under the [MIT License](LICENSE).
