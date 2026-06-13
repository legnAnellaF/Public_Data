from fastapi import APIRouter

from backend.app.schemas.common import APIStatus
from backend.app.services.public_api_registry import PublicApiRegistry

router = APIRouter(prefix="/api", tags=["categories"])
registry = PublicApiRegistry()


@router.get("/categories")
def categories() -> dict[str, object]:
    return {"status": APIStatus.OK.value, "categories": registry.list_categories()}


@router.get("/demo/queries")
def demo_queries() -> dict[str, object]:
    return {"status": APIStatus.OK.value, "queries": registry.demo_queries()}
