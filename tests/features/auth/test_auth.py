import pytest
from httpx import AsyncClient


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
