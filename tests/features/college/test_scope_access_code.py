from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_root import app
from app.features.auth.data.models.user_db import User
from app.features.auth.presentation.dependencies import get_current_user
from app.features.college.data.models.college_db import Batch, College, Department
from app.features.college.data.repositories import college_repository_impl
from app.features.college.presentation.schemas.college_dto import (
    AssignStaffScopeRequest,
    AssignStudentScopeRequest,
)


def test_scope_request_schemas_allow_missing_or_empty_access_code():
    department_id = uuid4()
    batch_id = uuid4()

    staff_request = AssignStaffScopeRequest(
        uid="staff-1",
        college_id="ukf",
        department_id=department_id,
    )
    student_request = AssignStudentScopeRequest(
        uid="student-1",
        college_id="ukf",
        access_code="",
        department_id=department_id,
        batch_id=batch_id,
    )

    assert staff_request.access_code is None
    assert student_request.access_code == ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("required_access_code", "provided_access_code"),
    [
        ("UKF2026", "UKF2026"),
        (None, "anything"),
    ],
)
async def test_assign_student_scope_allows_matching_or_unrestricted_access_code(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    required_access_code: str | None,
    provided_access_code: str,
):
    user, department, batch = await _seed_scope_models(db_session, role="student")
    monkeypatch.setattr(
        college_repository_impl,
        "_get_college_access_code",
        lambda college_id: required_access_code,
    )

    scope = await college_repository_impl.assign_student_scope(
        db_session,
        user.uid,
        "ukf",
        provided_access_code,
        department.id,
        batch.id,
    )

    assert scope.uid == user.uid
    assert scope.college_id == "ukf"
    assert scope.department_id == department.id
    assert scope.batch_id == batch.id


@pytest.mark.asyncio
async def test_assign_staff_scope_rejects_invalid_access_code(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, department, batch = await _seed_scope_models(db_session, role="hod")
    monkeypatch.setattr(
        college_repository_impl,
        "_get_college_access_code",
        lambda college_id: "UKF2026",
    )

    with pytest.raises(ValueError, match="invalid access code"):
        await college_repository_impl.assign_staff_scope(
            db_session,
            user.uid,
            "ukf",
            "wrong",
            department.id,
            batch.id,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_access_code", [None, ""])
async def test_assign_staff_scope_rejects_missing_access_code_when_college_requires_one(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    missing_access_code: str | None,
):
    user, department, batch = await _seed_scope_models(db_session, role="hod")
    monkeypatch.setattr(
        college_repository_impl,
        "_get_college_access_code",
        lambda college_id: "UKF2026",
    )

    with pytest.raises(ValueError, match="invalid access code"):
        await college_repository_impl.assign_staff_scope(
            db_session,
            user.uid,
            "ukf",
            missing_access_code,
            department.id,
            batch.id,
        )


@pytest.mark.asyncio
async def test_assign_staff_scope_endpoint_maps_invalid_access_code_to_403(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, department, batch = await _seed_scope_models(db_session, role="hod")

    async def override_current_user():
        return user

    monkeypatch.setattr(
        college_repository_impl,
        "_get_college_access_code",
        lambda college_id: "UKF2026",
    )
    app.dependency_overrides[get_current_user] = override_current_user

    response = await client.post(
        "/api/v1/scopes/staff",
        json={
            "uid": user.uid,
            "college_id": "ukf",
            "access_code": "wrong",
            "department_id": str(department.id),
            "batch_id": str(batch.id),
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "code": "INVALID_ACCESS_CODE",
            "message": "invalid access code",
        }
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_access_code", [None, ""])
async def test_assign_staff_scope_endpoint_maps_missing_required_access_code_to_403(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    missing_access_code: str | None,
):
    user, department, batch = await _seed_scope_models(db_session, role="hod")

    async def override_current_user():
        return user

    monkeypatch.setattr(
        college_repository_impl,
        "_get_college_access_code",
        lambda college_id: "UKF2026",
    )
    app.dependency_overrides[get_current_user] = override_current_user

    response = await client.post(
        "/api/v1/scopes/staff",
        json={
            "uid": user.uid,
            "college_id": "ukf",
            "access_code": missing_access_code,
            "department_id": str(department.id),
            "batch_id": str(batch.id),
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "code": "INVALID_ACCESS_CODE",
            "message": "invalid access code",
        }
    }


async def _seed_scope_models(
    db_session: AsyncSession,
    role: str,
) -> tuple[User, Department, Batch]:
    user = User(
        uid=f"{role}-{uuid4()}",
        name="Scoped User",
        email=f"{uuid4()}@example.com",
        role=role,
    )
    college = College(id="ukf", name="UKF College of Engineering", code="UKF")
    department_id = uuid4()
    batch_id = uuid4()
    department = Department(
        id=department_id,
        college_id="ukf",
        slug=f"cse-{uuid4()}",
        name="Computer Science",
    )
    batch = Batch(
        id=batch_id,
        department_id=department_id,
        label="2026-2030",
        start_year=2026,
        end_year=2030,
    )
    db_session.add_all([user, college, department, batch])
    await db_session.commit()
    await db_session.refresh(department)
    await db_session.refresh(batch)
    return user, department, batch
