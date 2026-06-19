#!/bin/bash
echo "=== pre-migrate ==="
python scripts/pre_migrate.py || echo "pre_migrate failed, continuing"

echo "=== alembic upgrade ==="
alembic upgrade head || echo "alembic upgrade failed, continuing"

echo "=== seed ==="
python -m app.scripts.seed_ukf || echo "seed failed, continuing"

echo "=== starting server ==="
exec uvicorn app.app_root:app --host 0.0.0.0 --port 8000 --workers 2
