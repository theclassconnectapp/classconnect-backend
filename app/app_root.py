from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config.app_settings import settings
from app.core.database.session import init_db
from app.core.utils.logger import configure_logging
from app.core.middlewares.logging_middleware import LoggingMiddleware
from app.core.middlewares.security_middleware import SecurityHeadersMiddleware
from app.core.errors.handlers import register_exception_handlers
from app.features.auth.presentation.api.auth_router import router as auth_router
# 👇 1. IMPORT YOUR NEW GEMINI ROUTER HERE
from app.features.ai.presentation.api.ai_router import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    yield


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ClassConnect API",
    version=settings.APP_VERSION,
    description="""
## ClassConnect Production Backend

Phase 1: Auth — Google OAuth, JWT, PostgreSQL users.

### Auth flow
1. Flutter calls `POST /auth/google` with Google ID token
2. Backend verifies token, creates/fetches user in PostgreSQL
3. Returns JWT access token (60min) + refresh token (30 days)
4. Flutter stores tokens locally (replace firebase_auth calls)
    """,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middlewares (order matters — outermost first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Exception handlers
register_exception_handlers(app)

# Routers
app.include_router(auth_router, prefix="/api/v1")
# 👇 2. MOUNT YOUR GEMINI ENGINE UNDER THE SAME API PREFIX
app.include_router(ai_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "service": "classconnect-api",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "phase": 1,
    }