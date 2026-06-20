from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database.session import get_db
from app.features.auth.presentation.schemas.auth_dto import (
    GoogleAuthRequest, TokenResponse, RefreshRequest,
    AppUserSchema, SaveUserRequest, FcmTokenRequest,
    VerifyRoleCodeRequest, VerifyRoleCodeResponse,
)
from app.features.auth.data.repositories.auth_repository_impl import (
    get_user, save_user, save_fcm_token,
)
from app.features.auth.domain.usecases import login_with_google, verify_role_code
from app.features.auth.domain.usecases.login_with_google import user_to_schema
from app.core.security.jwt_handler import (
    create_access_token, create_refresh_token, verify_token,
)
from app.features.auth.presentation.dependencies import get_current_user
from app.features.auth.data.models.user_db import User
from app.core.config.app_settings import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import structlog

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Auth"])


def _verify_google_token(token: str) -> dict:
    """
    Verifies Google ID token from Flutter GoogleSignIn.
    Returns: {uid, email, name, photo_url}
    """
    try:
        info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        return {
            "uid": info["sub"],
            "email": info.get("email", ""),
            "name": info.get("name", ""),
            "photo_url": info.get("picture"),
        }
    except Exception as exc:
        logger.warning("google_token_invalid", error=str(exc))
        raise ValueError(f"Invalid Google token: {exc}")


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Sign in with Google",
    description="Flutter sends Google ID token. Returns JWT access+refresh tokens and user profile.",
)
@limiter.limit("10/minute")
async def sign_in_with_google(
    request: Request,
    req: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        google_data = _verify_google_token(req.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"code": "INVALID_GOOGLE_TOKEN", "message": str(exc)})

    token_response, is_new = await login_with_google.execute(db, google_data, req.college_id)
    logger.info("user_signed_in", uid=google_data["uid"], is_new=is_new)
    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh JWT tokens",
    description="Silent token refresh. Mirrors Firebase Auth auto token refresh.",
)
@limiter.limit("20/minute")
async def refresh_tokens(
    request: Request,
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    uid = verify_token(req.refresh_token, token_type="refresh")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"},
        )
    user = await get_user(db, uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "USER_NOT_FOUND", "message": "User not found"})

    return TokenResponse(
        access_token=create_access_token(uid),
        refresh_token=create_refresh_token(uid),
        user=user_to_schema(user),
    )


@router.post(
    "/verify-role-code",
    response_model=VerifyRoleCodeResponse,
    summary="Verify role invite code",
    description="Returns the role associated with a valid advisor/HOD invite code.",
)
async def verify_role_invite_code(req: VerifyRoleCodeRequest):
    role = verify_role_code.execute(req.code)
    return VerifyRoleCodeResponse(valid=role is not None, role=role)


@router.get(
    "/me",
    response_model=AppUserSchema,
    summary="Get current user",
    description="Returns authenticated user profile. Mirrors UserRepository.getUser(uid).",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return user_to_schema(current_user)


@router.post(
    "/user/save",
    response_model=AppUserSchema,
    summary="Save user profile",
    description="Upserts full profile. Called from ProfileSetupScreen after role/dept/batch selection.",
)
async def save_user_profile(
    req: SaveUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"code": "PERMISSION_DENIED", "message": "Cannot modify another user"})
    user = await save_user(db, req)
    return user_to_schema(user)


@router.post(
    "/user/fcm-token",
    summary="Register FCM token",
    description="Saves FCM push token. Mirrors UserRepository.saveFcmToken().",
)
async def update_fcm_token(
    req: FcmTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.uid != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"code": "PERMISSION_DENIED", "message": "Forbidden"})
    await save_fcm_token(db, req.uid, req.token)
    return {"status": "ok"}


@router.post(
    "/signout",
    summary="Sign out",
    description="Server-side sign out. JWT is stateless — client must delete tokens locally.",
)
async def sign_out(current_user: User = Depends(get_current_user)):
    logger.info("user_signed_out", uid=current_user.uid)
    return {"status": "signed_out"}
