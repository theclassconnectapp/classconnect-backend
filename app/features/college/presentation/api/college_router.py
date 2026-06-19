from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.features.auth.data.models.user_db import User
from app.features.auth.presentation.dependencies import get_current_user
from app.features.college.data.repositories.college_repository_impl import (
    create_department,
    list_batches,
    list_departments,
)
from app.features.college.domain.usecases import assign_staff_scope, assign_student_scope, get_user_scopes
from app.features.college.presentation.schemas.college_dto import (
    AssignStaffScopeRequest,
    AssignStudentScopeRequest,
    BatchSchema,
    CreateDepartmentRequest,
    DepartmentSchema,
    UserScopeSchema,
    UserScopesResponse,
)

logger = structlog.get_logger()
router = APIRouter(tags=["College"])


def _bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "INVALID_SCOPE", "message": message},
    )


@router.get(
    "/colleges/{college_id}/departments",
    response_model=list[DepartmentSchema],
    summary="List departments for a college",
)
async def list_college_departments(
    college_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_departments(db, college_id)


@router.get(
    "/departments/{department_id}/batches",
    response_model=list[BatchSchema],
    summary="List batches for a department",
)
async def list_department_batches(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_batches(db, department_id)


@router.post(
    "/departments",
    response_model=DepartmentSchema,
    summary="Create a department",
)
async def create_department_endpoint(
    req: CreateDepartmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # TODO: Replace this placeholder with a proper college-admin role in a later phase.
    if current_user.role != "hod":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Only HOD users can create departments"},
        )
    try:
        return await create_department(
            db,
            req.college_id,
            req.slug,
            req.name,
            req.code,
            current_user.uid,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DEPARTMENT_EXISTS", "message": "Department already exists for this college"},
        )


@router.post(
    "/scopes/student",
    response_model=UserScopeSchema,
    summary="Assign a locked student/advisor scope",
)
async def assign_student_scope_endpoint(
    req: AssignStudentScopeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Cannot modify another user"},
        )
    try:
        return await assign_student_scope.execute(
            db,
            req.uid,
            req.college_id,
            req.department_id,
            req.batch_id,
        )
    except ValueError as exc:
        if "immutable" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "SCOPE_ALREADY_ASSIGNED", "message": str(exc)},
            )
        raise _bad_request(str(exc))


@router.post(
    "/scopes/staff",
    response_model=UserScopeSchema,
    summary="Assign an additive staff scope",
)
async def assign_staff_scope_endpoint(
    req: AssignStaffScopeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Cannot modify another user"},
        )
    if current_user.role not in ("hod", "subjectTeacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Only staff users can assign staff scopes"},
        )
    try:
        return await assign_staff_scope.execute(
            db,
            req.uid,
            req.college_id,
            req.department_id,
            req.batch_id,
        )
    except ValueError as exc:
        raise _bad_request(str(exc))


@router.get(
    "/scopes/me",
    response_model=UserScopesResponse,
    summary="Get scopes for current user",
)
async def get_my_scopes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await get_user_scopes.execute(db, current_user.uid)
    return UserScopesResponse(
        kind=result.kind,
        scopes=[UserScopeSchema.model_validate(scope) for scope in result.scopes],
    )
