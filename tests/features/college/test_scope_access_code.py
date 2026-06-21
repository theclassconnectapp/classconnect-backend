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
async def test_assign_student_scope_creates_general_group_when_missing(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, department, batch = await _seed_scope_models(db_session, role="student")
    firestore_client = FakeFirestoreClient()
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setattr(college_repository_impl, "_get_firebase_app", lambda: object())
    monkeypatch.setattr(college_repository_impl.firestore, "client", lambda app: firestore_client)
    monkeypatch.setattr(college_repository_impl, "_get_college_access_code", lambda college_id: None)

    await college_repository_impl.assign_student_scope(
        db_session,
        user.uid,
        "ukf",
        None,
        department.id,
        batch.id,
    )

    group_ref = firestore_client.collection("colleges/ukf/groups").document(f"{batch.id}_general")
    assert group_ref.set_count == 1
    assert group_ref.data == {
        "id": f"{batch.id}_general",
        "name": "General",
        "description": f"General group for {batch.label}",
        "collegeId": "ukf",
        "dept": department.name,
        "batch": batch.label,
        "departmentId": str(department.id),
        "batchId": str(batch.id),
        "createdAt": college_repository_impl.firestore.SERVER_TIMESTAMP,
        "isGeneral": True,
        "archived": False,
        "members": [],
    }


@pytest.mark.asyncio
async def test_assign_student_scope_does_not_create_duplicate_general_group(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, department, batch = await _seed_scope_models(db_session, role="student")
    firestore_client = FakeFirestoreClient()
    group_ref = firestore_client.collection("colleges/ukf/groups").document(f"{batch.id}_general")
    existing_data = {
        "id": f"{batch.id}_general",
        "name": "General With Activity",
        "members": ["student-1"],
    }
    group_ref.data = existing_data.copy()
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setattr(college_repository_impl, "_get_firebase_app", lambda: object())
    monkeypatch.setattr(college_repository_impl.firestore, "client", lambda app: firestore_client)
    monkeypatch.setattr(college_repository_impl, "_get_college_access_code", lambda college_id: None)

    await college_repository_impl.assign_student_scope(
        db_session,
        user.uid,
        "ukf",
        None,
        department.id,
        batch.id,
    )

    assert group_ref.set_count == 0
    assert group_ref.data == existing_data


@pytest.mark.asyncio
async def test_assign_student_scope_ignores_general_group_firestore_failure(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, department, batch = await _seed_scope_models(db_session, role="student")
    firestore_client = FakeFirestoreClient(fail_on_get=True)
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setattr(college_repository_impl, "_get_firebase_app", lambda: object())
    monkeypatch.setattr(college_repository_impl.firestore, "client", lambda app: firestore_client)
    monkeypatch.setattr(college_repository_impl, "_get_college_access_code", lambda college_id: None)

    scope = await college_repository_impl.assign_student_scope(
        db_session,
        user.uid,
        "ukf",
        None,
        department.id,
        batch.id,
    )

    assert scope.uid == user.uid
    assert scope.department_id == department.id
    await db_session.refresh(user)
    assert user.department_id == department.id
    assert user.batch_id == batch.id


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


class FakeFirestoreClient:
    def __init__(self, fail_on_get: bool = False):
        self.collections = {}
        self.fail_on_get = fail_on_get

    def collection(self, path):
        if path not in self.collections:
            self.collections[path] = FakeCollectionReference(self.fail_on_get)
        return self.collections[path]


class FakeCollectionReference:
    def __init__(self, fail_on_get: bool):
        self.documents = {}
        self.fail_on_get = fail_on_get

    def document(self, document_id):
        if document_id not in self.documents:
            self.documents[document_id] = FakeDocumentReference(self.fail_on_get)
        return self.documents[document_id]


class FakeDocumentReference:
    def __init__(self, fail_on_get: bool):
        self.data = None
        self.set_count = 0
        self.fail_on_get = fail_on_get

    def get(self):
        if self.fail_on_get:
            raise RuntimeError("firestore unavailable")
        return FakeDocumentSnapshot(exists=self.data is not None)

    def set(self, data):
        self.data = data.copy()
        self.set_count += 1


class FakeDocumentSnapshot:
    def __init__(self, exists):
        self.exists = exists
