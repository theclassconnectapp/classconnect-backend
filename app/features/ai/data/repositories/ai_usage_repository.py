from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai.data.models.ai_usage_db import AiUsage


async def count_today(db: AsyncSession, uid: str) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(func.count())
        .select_from(AiUsage)
        .where(AiUsage.uid == uid, AiUsage.used_at >= cutoff)
    )
    return int(result.scalar_one())


async def record_usage(db: AsyncSession, uid: str) -> None:
    db.add(AiUsage(uid=uid))
    await db.commit()
