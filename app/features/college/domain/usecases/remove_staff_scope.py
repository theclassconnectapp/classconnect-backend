from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.college.data.repositories.college_repository_impl import (
    remove_staff_scope as remove_staff_scope_repo,
)


async def execute(db: AsyncSession, uid: str, scope_id: UUID) -> None:
    await remove_staff_scope_repo(db, uid, scope_id)
