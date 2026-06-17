import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes_categories import router as categories_router
from backend.app.api.routes_datasets import router as datasets_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_intent import router as intent_router
from backend.app.api.routes_widget import router as widget_router
from backend.app.config import get_settings
from backend.app.logging_config import configure_logging
from backend.app.schemas.common import APIStatus

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Public data search and visualization widget backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"^(chrome-extension|moz-extension)://.*$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(categories_router)
app.include_router(datasets_router)
app.include_router(intent_router)
app.include_router(widget_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("request_validation_error path=%s", request.url.path)
    return JSONResponse(
        status_code=422,
        content={
            "status": APIStatus.ERROR.value,
            "message": "요청 형식이 올바르지 않습니다.",
            "error_code": "VALIDATION_ERROR",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error path=%s error=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "status": APIStatus.ERROR.value,
            "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )
