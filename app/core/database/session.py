from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config.app_settings import settings


def get_async_database_url(database_url: str) -> str:
    url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL),
    echo=settings.APP_ENV == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # reconnect after DB restart (important for AWS RDS)
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables for local dev/test convenience. Production uses Alembic migrations only."""
    if settings.is_production:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
