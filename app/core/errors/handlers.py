from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.errors.exceptions import ClassConnectException
import structlog

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ClassConnectException)
    async def classconnect_exception_handler(
        request: Request, exc: ClassConnectException
    ) -> JSONResponse:
        logger.warning("app_error", code=exc.code, message=exc.message,
                       path=str(request.url))
        status_map = {
            "AUTH_ERROR": 401,
            "INVALID_TOKEN": 401,
            "USER_NOT_FOUND": 404,
            "PERMISSION_DENIED": 403,
        }
        return JSONResponse(
            status_code=status_map.get(exc.code, 500),
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        logger.warning("validation_error", errors=errors, path=str(request.url))
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "errors": errors}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("unhandled_error", exc=str(exc), path=str(request.url))
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
        )
