from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.college.data.repositories.college_repository_impl import (
    assign_student_scope as assign_student_scope_repo,
)
from app.features.college.domain.entities.college import UserScope


class StudentScopeAlreadyAssignedError(ValueError):
    pass


async def execute(
    db: AsyncSession,
    uid: str,
    college_id: str,
    department_id: UUID,
    batch_id: UUID,
) -> UserScope:
    return await assign_student_scope_repo(db, uid, college_id, department_id, batch_id)
