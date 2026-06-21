import asyncio
import os
from typing import Optional
from uuid import UUID

import structlog
from firebase_admin import firestore
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.firebase_auth import _get_firebase_app
from app.features.auth.data.models.user_db import User
from app.features.college.data.models.college_db import Batch, College, Department
from app.features.college.data.models.user_scope_db import UserScope
from app.features.college.domain.entities.college import (
    Batch as BatchEntity,
    College as CollegeEntity,
    Department as DepartmentEntity,
    UserScope as UserScopeEntity,
)
from app.features.college.domain.entities.user_scopes_result import UserScopesResult

logger = structlog.get_logger()


def _college_to_entity(college: College) -> CollegeEntity:
    return CollegeEntity(
        id=college.id,
        name=college.name,
        code=college.code,
        active=college.active,
        created_at=college.created_at,
        updated_at=college.updated_at,
    )


def _department_to_entity(department: Department) -> DepartmentEntity:
    return DepartmentEntity(
        id=department.id,
        college_id=department.college_id,
        slug=department.slug,
        name=department.name,
        code=department.code,
        created_at=department.created_at,
        created_by=department.created_by,
    )


def _batch_to_entity(batch: Batch) -> BatchEntity:
    return BatchEntity(
        id=batch.id,
        department_id=batch.department_id,
        label=batch.label,
        start_year=batch.start_year,
        end_year=batch.end_year,
        archived=batch.archived,
        created_at=batch.created_at,
    )


def _scope_to_entity(scope: UserScope) -> UserScopeEntity:
    return UserScopeEntity(
        id=scope.id,
        uid=scope.uid,
        college_id=scope.college_id,
        department_id=scope.department_id,
        batch_id=scope.batch_id,
        created_at=scope.created_at,
    )


async def get_college(db: AsyncSession, college_id: str) -> CollegeEntity | None:
    result = await db.execute(select(College).where(College.id == college_id))
    college = result.scalar_one_or_none()
    return _college_to_entity(college) if college else None


async def list_departments(db: AsyncSession, college_id: str) -> list[DepartmentEntity]:
    result = await db.execute(
        select(Department)
        .where(Department.college_id == college_id)
        .order_by(Department.name)
    )
    return [_department_to_entity(department) for department in result.scalars().all()]


async def get_department(db: AsyncSession, department_id: UUID) -> DepartmentEntity | None:
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    return _department_to_entity(department) if department else None


async def list_batches(db: AsyncSession, department_id: UUID) -> list[BatchEntity]:
    result = await db.execute(
        select(Batch)
        .where(Batch.department_id == department_id)
        .order_by(Batch.start_year)
    )
    return [_batch_to_entity(batch) for batch in result.scalars().all()]


async def get_batch(db: AsyncSession, batch_id: UUID) -> BatchEntity | None:
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    return _batch_to_entity(batch) if batch else None


async def create_department(
    db: AsyncSession,
    college_id: str,
    slug: str,
    name: str,
    code: Optional[str],
    created_by: Optional[str],
) -> DepartmentEntity:
    department = Department(
        college_id=college_id,
        slug=slug.strip().lower(),
        name=name.strip(),
        code=code,
        created_by=created_by,
    )
    db.add(department)
    try:
        await db.commit()
        await db.refresh(department)
    except IntegrityError:
        await db.rollback()
        logger.warning("department_create_failed", college_id=college_id, slug=slug)
        raise
    logger.info("department_created", department_id=str(department.id), college_id=college_id)
    return _department_to_entity(department)


async def seed_batches_for_department(
    db: AsyncSession,
    department_id: UUID,
    start_year: int,
    count: int = 5,
) -> list[BatchEntity]:
    created_batches: list[Batch] = []
    for offset in range(count):
        year = start_year + offset
        batch = Batch(
            department_id=department_id,
            label=f"{year}-{year + 4}",
            start_year=year,
            end_year=year + 4,
        )
        db.add(batch)
        created_batches.append(batch)
    try:
        await db.commit()
        for batch in created_batches:
            await db.refresh(batch)
    except IntegrityError:
        await db.rollback()
        logger.warning("batch_seed_failed", department_id=str(department_id), start_year=start_year)
        raise
    logger.info("batches_seeded", department_id=str(department_id), count=len(created_batches))
    return [_batch_to_entity(batch) for batch in created_batches]


async def _get_user(db: AsyncSession, uid: str) -> User:
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
    return user


async def _get_department_model(db: AsyncSession, department_id: UUID) -> Department:
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise ValueError("Department not found")
    return department


async def _get_batch_model(db: AsyncSession, batch_id: UUID) -> Batch:
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if batch is None:
        raise ValueError("Batch not found")
    return batch


async def _validate_scope(
    db: AsyncSession,
    college_id: str,
    department_id: UUID,
    batch_id: Optional[UUID],
) -> tuple[Department, Batch | None]:
    department = await _get_department_model(db, department_id)
    if department.college_id != college_id:
        raise ValueError("Department does not belong to the requested college")

    batch = None
    if batch_id is not None:
        batch = await _get_batch_model(db, batch_id)
        if batch.department_id != department_id:
            raise ValueError("Batch does not belong to the requested department")
    return department, batch


def _get_college_access_code(college_id: str) -> str | None:
    app = _get_firebase_app()
    db = firestore.client(app=app)
    snapshot = db.collection("colleges").document(college_id).get()
    if not snapshot.exists:
        return None

    access_code = (snapshot.to_dict() or {}).get("accessCode")
    return access_code if isinstance(access_code, str) else None


async def _validate_college_access_code(college_id: str, access_code: Optional[str]) -> None:
    required_access_code = await asyncio.to_thread(_get_college_access_code, college_id)
    if required_access_code is not None and required_access_code != access_code:
        raise ValueError("invalid access code")


def _ensure_general_group_exists_sync(
    college_id: str,
    department_id: UUID,
    batch_id: UUID | None,
    department_name: str,
    batch_label: str | None,
) -> None:
    if not os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"):
        return

    group_id = f"{batch_id}_general" if batch_id else f"{department_id}_general"
    group_label = batch_label or department_name
    app = _get_firebase_app()
    db = firestore.client(app=app)
    group_ref = db.collection(f"colleges/{college_id}/groups").document(group_id)

    existing = group_ref.get()
    if existing.exists:
        return

    group_ref.set(
        {
            "id": group_id,
            "name": "General",
            "description": f"General group for {group_label}",
            "collegeId": college_id,
            "dept": department_name,
            "batch": batch_label or "",
            "departmentId": str(department_id),
            "batchId": str(batch_id) if batch_id else None,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "isGeneral": True,
            "archived": False,
            "members": [],
        }
    )


async def _ensure_general_group_exists(
    college_id: str,
    department_id: UUID,
    batch_id: UUID | None,
    department_name: str,
    batch_label: str | None,
) -> None:
    try:
        await asyncio.to_thread(
            _ensure_general_group_exists_sync,
            college_id,
            department_id,
            batch_id,
            department_name,
            batch_label,
        )
    except Exception as exc:
        logger.warning(
            "general_group_ensure_failed",
            college_id=college_id,
            department_id=str(department_id),
            batch_id=str(batch_id) if batch_id else None,
            exc_info=exc,
        )


async def assign_student_scope(
    db: AsyncSession,
    uid: str,
    college_id: str,
    access_code: Optional[str],
    department_id: UUID,
    batch_id: UUID,
) -> UserScopeEntity:
    user = await _get_user(db, uid)
    if user.department_id is not None:
        raise ValueError("Student scope is immutable once assigned")

    await _validate_college_access_code(college_id, access_code)
    department, batch = await _validate_scope(db, college_id, department_id, batch_id)
    if batch is None:
        raise ValueError("Batch is required for student scope")

    user.college_id = college_id
    user.department_id = department_id
    user.batch_id = batch_id
    user.dept = department.name
    user.batch = batch.label
    await db.commit()
    await db.refresh(user)
    await _ensure_general_group_exists(
        college_id,
        department_id,
        batch_id,
        department.name,
        batch.label,
    )
    logger.info("student_scope_assigned", uid=uid, department_id=str(department_id), batch_id=str(batch_id))
    return UserScopeEntity(
        id=None,
        uid=user.uid,
        college_id=college_id,
        department_id=department_id,
        batch_id=batch_id,
    )


async def assign_staff_scope(
    db: AsyncSession,
    uid: str,
    college_id: str,
    access_code: Optional[str],
    department_id: UUID,
    batch_id: Optional[UUID] = None,
) -> UserScopeEntity:
    await _get_user(db, uid)
    await _validate_college_access_code(college_id, access_code)
    department, batch = await _validate_scope(db, college_id, department_id, batch_id)

    scope = UserScope(
        uid=uid,
        college_id=college_id,
        department_id=department_id,
        batch_id=batch_id,
    )
    db.add(scope)
    await db.commit()
    await db.refresh(scope)
    await _ensure_general_group_exists(
        college_id,
        department_id,
        batch_id,
        department.name,
        batch.label if batch else None,
    )
    logger.info("staff_scope_assigned", uid=uid, department_id=str(department_id), batch_id=str(batch_id))
    return _scope_to_entity(scope)


async def remove_staff_scope(db: AsyncSession, uid: str, scope_id: UUID) -> None:
    result = await db.execute(select(UserScope).where(UserScope.id == scope_id))
    scope = result.scalar_one_or_none()
    if scope is None:
        raise ValueError("scope not found")
    if scope.uid != uid:
        raise ValueError("not authorized to remove this scope")

    await db.delete(scope)
    await db.commit()
    logger.info("staff_scope_removed", uid=uid, scope_id=str(scope_id))


async def get_user_scopes(db: AsyncSession, uid: str) -> UserScopesResult:
    user = await _get_user(db, uid)
    if user.role in ("student", "advisor"):
        scopes = []
        if user.college_id and user.department_id and user.batch_id:
            scopes.append(
                UserScopeEntity(
                    id=None,
                    uid=user.uid,
                    college_id=user.college_id,
                    department_id=user.department_id,
                    batch_id=user.batch_id,
                )
            )
        return UserScopesResult(kind="locked", scopes=scopes)

    result = await db.execute(
        select(UserScope)
        .where(UserScope.uid == uid)
        .order_by(UserScope.created_at)
    )
    return UserScopesResult(
        kind="staff",
        scopes=[_scope_to_entity(scope) for scope in result.scalars().all()],
    )
