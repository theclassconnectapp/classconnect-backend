from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.features.ai.domain.ai_service import AIService

# Set to just /ai because app_root adds the /api/v1 prefix automatically!
router = APIRouter(prefix="/ai", tags=["Gemini Engine"])

class PromptRequest(BaseModel):
    prompt: str

def get_ai_service() -> AIService:
    return AIService()

@router.post("/generate")
async def generate_ai_content(
    request: PromptRequest, 
    service: AIService = Depends(get_ai_service)
):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    response_text = await service.generate_response(request.prompt)
    return {"status": "success", "data": response_text}
