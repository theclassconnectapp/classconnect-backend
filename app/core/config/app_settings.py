from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str

    # 👇 GEMINI CLOUD AI CONFIGURATION
    GEMINI_API_KEY: str = "mock-key"
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"

    # App
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Extra fields option if you want safety against unexpected env inputs:
        extra = "ignore" 


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()