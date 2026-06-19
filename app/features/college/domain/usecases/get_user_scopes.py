from sqlalchemy.ext.asyncio import AsyncSession

from app.features.college.data.repositories.college_repository_impl import (
    get_user_scopes as get_user_scopes_repo,
)
from app.features.college.domain.entities.user_scopes_result import UserScopesResult


async def execute(db: AsyncSession, uid: str) -> UserScopesResult:
    return await get_user_scopes_repo(db, uid)
