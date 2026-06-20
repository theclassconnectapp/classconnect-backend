from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from app.features.auth.data.models.user_db import User
from app.features.auth.presentation.schemas.auth_dto import SaveUserRequest
from app.core.errors.exceptions import UserNotFoundException
import structlog

logger = structlog.get_logger()


async def get_user(db: AsyncSession, uid: str) -> User | None:
    result = await db.execute(select(User).where(User.uid == uid))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession,
    uid: str,
    name: str,
    email: str,
) -> User:
    user = await get_user(db, uid)
    if user is not None:
        return user

    user = User(
        uid=uid,
        name=name,
        email=email,
        role="student",
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        logger.info("user_created", uid=user.uid, email=user.email)
    except IntegrityError:
        # Race condition: another request created the user between get and insert
        await db.rollback()
        user = await get_user(db, uid)
    return user


async def get_or_create_google_user(
    db: AsyncSession,
    google_data: dict,
    college_id: str | None,
) -> tuple[User, bool]:
    """
    Returns (user, is_new).
    Mirrors Firebase Auth trigger that created a Firestore doc on first sign-in.
    """
    user = await get_user(db, google_data["uid"])
    if user is not None:
        return user, False

    user = await get_or_create_user(
        db,
        google_data["uid"],
        google_data.get("name", ""),
        google_data.get("email", ""),
    )
    user.photo_url = google_data.get("photo_url")
    user.college_id = college_id
    await db.commit()
    await db.refresh(user)
    return user, True


async def save_user(db: AsyncSession, req: SaveUserRequest) -> User:
    """
    Full upsert. Mirrors UserRepository.saveUser().
    Called from ProfileSetupScreen after role/dept/batch selection.
    """
    user = await get_user(db, req.uid)
    if user is None:
        user = User(
            uid=req.uid, name=req.name, email=req.email,
            role=req.role, dept=req.dept, batch=req.batch,
            photo_url=req.photo_url, college_id=req.college_id,
        )
        db.add(user)
    else:
        user.name = req.name
        user.email = req.email
        user.role = req.role
        user.dept = req.dept
        user.batch = req.batch
        user.photo_url = req.photo_url
        if req.college_id:
            user.college_id = req.college_id

    await db.commit()
    await db.refresh(user)
    logger.info("user_saved", uid=user.uid, role=user.role)
    return user


async def update_user_role(db: AsyncSession, uid: str, role: str) -> User | None:
    await db.execute(
        update(User)
        .where(User.uid == uid)
        .values(role=role, updated_at=func.now())
    )
    await db.commit()
    user = await get_user(db, uid)
    if user is not None:
        logger.info("user_role_updated", uid=user.uid, role=user.role)
    return user


async def save_fcm_token(db: AsyncSession, uid: str, token: str) -> None:
    """Mirrors UserRepository.saveFcmToken()."""
    user = await get_user(db, uid)
    if user is None:
        raise UserNotFoundException(uid)
    user.fcm_token = token
    await db.commit()
    logger.info("fcm_token_saved", uid=uid)
