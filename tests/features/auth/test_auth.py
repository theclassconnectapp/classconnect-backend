import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.data.models.user_db import User
from app.features.auth.data.repositories.auth_repository_impl import get_user
from app.features.auth.presentation import dependencies as auth_dependencies


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_google_signin_empty_token(client: AsyncClient):
    r = await client.post("/api/v1/auth/google", json={"id_token": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_refresh_empty_token(client: AsyncClient):
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_me_no_auth(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_verify_role_code_endpoint_exists(client: AsyncClient):
    r = await client.post("/api/v1/auth/verify-role-code", json={"code": "UNKNOWN"})
    assert r.status_code == 200
    assert r.json() == {"valid": False, "role": None}


@pytest.mark.asyncio
async def test_verify_role_code_updates_authenticated_user_role(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    db_session.add(
        User(
            uid="staff-uid",
            name="Staff User",
            email="staff@example.com",
            role="student",
        )
    )
    await db_session.commit()
    monkeypatch.setattr(auth_dependencies, "verify_firebase_token", lambda token: "staff-uid")

    r = await client.post(
        "/api/v1/auth/verify-role-code",
        json={"code": "TEACH2025"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert r.status_code == 200
    assert r.json() == {"valid": True, "role": "subjectTeacher"}

    user = await get_user(db_session, "staff-uid")
    assert user is not None
    assert user.role == "subjectTeacher"


@pytest.mark.asyncio
async def test_me_auto_creates_firebase_user(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(auth_dependencies, "verify_firebase_token", lambda token: "firebase-uid")
    monkeypatch.setattr(
        auth_dependencies,
        "decode_firebase_token",
        lambda token: {"uid": "firebase-uid", "name": "Firebase User", "email": "firebase@example.com"},
    )

    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test-token"})

    assert r.status_code == 200
    assert r.json()["uid"] == "firebase-uid"
    assert r.json()["role"] == "student"

    user = await get_user(db_session, "firebase-uid")
    assert user is not None
    assert user.name == "Firebase User"
    assert user.email == "firebase@example.com"
    assert user.role == "student"
