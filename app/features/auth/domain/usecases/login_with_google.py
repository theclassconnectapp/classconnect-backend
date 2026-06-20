"""
UseCase: LoginWithGoogle
Input:  Verified Google payload + optional college_id
Output: JWT tokens + AppUser
Mirrors: AuthRemoteDataSource.signInWithGoogle()
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.data.repositories.auth_repository_impl import get_or_create_google_user
from app.core.security.jwt_handler import create_access_token, create_refresh_token
from app.features.auth.presentation.schemas.auth_dto import TokenResponse, AppUserSchema
from app.features.auth.data.models.user_db import User


def user_to_schema(user: User) -> AppUserSchema:
    return AppUserSchema(
        uid=user.uid, name=user.name, email=user.email,
        role=user.role, dept=user.dept, batch=user.batch,
        photo_url=user.photo_url, college_id=user.college_id,
    )


async def execute(
    db: AsyncSession,
    google_data: dict,
    college_id: str | None,
) -> tuple[TokenResponse, bool]:
    """Returns (TokenResponse, is_new_user)."""
    user, is_new = await get_or_create_google_user(db, google_data, college_id)
    token_response = TokenResponse(
        access_token=create_access_token(user.uid),
        refresh_token=create_refresh_token(user.uid),
        is_new_user=is_new,
        user=user_to_schema(user),
    )
    return token_response, is_new
