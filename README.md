# ClassConnect Backend

Production FastAPI backend replacing Firebase — built phase by phase.

## Phase 1 — Auth ✅
Google OAuth → JWT (access + refresh) → PostgreSQL

## Stack
| Layer | Tech |
|-------|------|
| Framework | FastAPI + uvicorn |
| Database | PostgreSQL (asyncpg + SQLAlchemy async) |
| Migrations | Alembic |
| Auth | Google OAuth2 + JWT (python-jose) |
| Rate limiting | slowapi |
| Logging | structlog (JSON in prod, pretty in dev) |
| Security | HSTS, XSS, CSP headers |
| Deployment | Docker → AWS ECS |

## Run locally
```bash
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID and SECRET_KEY
docker-compose up
```

## Migrations
```bash
# Auto-generate after model changes
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

## Tests
```bash
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v
```

## AWS deploy (Phase 2)
- Push image to AWS ECR
- Run on ECS Fargate
- DATABASE_URL points to RDS PostgreSQL
- Secrets via AWS Secrets Manager → ECS env vars

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/google | Google sign-in → JWT |
| POST | /api/v1/auth/refresh | Silent token refresh |
| GET  | /api/v1/auth/me | Current user profile |
| POST | /api/v1/auth/user/save | Save profile (ProfileSetupScreen) |
| POST | /api/v1/auth/user/fcm-token | Register FCM token |
| POST | /api/v1/auth/signout | Sign out |
| GET  | /health | Health check |

Docs: http://localhost:8000/docs
