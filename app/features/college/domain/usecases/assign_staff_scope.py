from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.college.data.repositories.college_repository_impl import (
    assign_staff_scope as assign_staff_scope_repo,
)
from app.features.college.domain.entities.college import UserScope


async def execute(
    db: AsyncSession,
    uid: str,
    college_id: str,
    access_code: Optional[str],
    department_id: UUID,
    batch_id: Optional[UUID] = None,
) -> UserScope:
    return await assign_staff_scope_repo(db, uid, college_id, access_code, department_id, batch_id)
