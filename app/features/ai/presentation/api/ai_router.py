from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.features.ai.data.repositories.ai_usage_repository import count_today, record_usage
from app.features.ai.domain.ai_service import AIService
from app.features.auth.data.models.user_db import User
from app.features.auth.presentation.dependencies import get_current_user

# Set to just /ai because app_root adds the /api/v1 prefix automatically!
router = APIRouter(prefix="/ai", tags=["Gemini Engine"])

class PromptRequest(BaseModel):
    prompt: str

def get_ai_service() -> AIService:
    return AIService()

@router.post("/generate")
async def generate_ai_content(
    request: PromptRequest, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    usage_count = await count_today(db, current_user.uid)
    if usage_count >= 5:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "code": "RATE_LIMITED",
                "message": "Daily AI limit reached. Resets in 24 hours.",
            },
        )
    
    response_text = await service.generate_response(request.prompt)
    await record_usage(db, current_user.uid)
    return {"status": "success", "data": response_text}
