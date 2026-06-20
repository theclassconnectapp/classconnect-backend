import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai.data.models.ai_usage_db import AiUsage
from app.features.ai.presentation.api.ai_router import get_ai_service
from app.features.auth.data.models.user_db import User
from app.features.auth.presentation.dependencies import get_current_user
from app.app_root import app


class FakeAIService:
    def __init__(self):
        self.calls = 0

    async def generate_response(self, user_prompt: str) -> str:
        self.calls += 1
        return f"response: {user_prompt}"


@pytest.mark.asyncio
async def test_generate_ai_content_limits_user_to_five_requests_per_24_hours(
    client: AsyncClient,
    db_session: AsyncSession,
):
    user = User(
        uid="ai-user",
        name="AI User",
        email="ai-user@example.com",
        role="student",
    )
    db_session.add(user)
    await db_session.commit()

    fake_service = FakeAIService()

    async def override_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_ai_service] = lambda: fake_service

    for _ in range(5):
        response = await client.post("/api/v1/ai/generate", json={"prompt": "Explain limits"})
        assert response.status_code == 200

    limited_response = await client.post("/api/v1/ai/generate", json={"prompt": "One more"})

    assert limited_response.status_code == 429
    assert limited_response.json() == {
        "code": "RATE_LIMITED",
        "message": "Daily AI limit reached. Resets in 24 hours.",
    }
    assert fake_service.calls == 5

    usage_count = await db_session.scalar(
        select(func.count()).select_from(AiUsage).where(AiUsage.uid == user.uid)
    )
    assert usage_count == 5
