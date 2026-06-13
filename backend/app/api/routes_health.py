from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.schemas.common import APIStatus

router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": APIStatus.OK.value,
        "service": settings.app_name,
        "version": settings.version,
        "mock_mode": settings.mock_public_api,
    }
