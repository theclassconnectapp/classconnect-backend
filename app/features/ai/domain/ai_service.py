from google import genai
from google.genai import types
from app.core.config.app_settings import settings

class AIService:
    def __init__(self):
        # Explicitly fallback to standard environment lookups if settings isn't populated
        import os
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=api_key)
        self.model = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-2.5-flash')

    async def generate_response(self, user_prompt: str) -> str:
        system_instruction = (
            "You are ClassConnect AI, an intelligent, helpful, and concise assistant "
            "integrated into a college management app. Assist students and founders "
            "with precise technical, academic, or logistical information. "
            "Keep your tone professional, adaptive, and highly direct. Avoid fluff."
        )
        try:
            # Running synchronous SDK call inside an async wrapper or executing directly
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            return f"AI Generation Cloud Error: {str(e)}"
