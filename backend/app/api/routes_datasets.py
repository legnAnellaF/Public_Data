import logging
import time

from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.schemas.common import APIStatus, MetaInfo
from backend.app.schemas.datasets import DatasetSearchItem, DatasetSearchRequest, DatasetSearchResponse
from backend.app.services.dataset_search import search_public_datasets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["datasets"])


def _elapsed_ms(started_at: float) -> int:
    return max(0, int((time.perf_counter() - started_at) * 1000))


def _search(request: DatasetSearchRequest) -> DatasetSearchResponse:
    started_at = time.perf_counter()
    settings = get_settings()

    if not settings.enable_dynamic_public_data:
        return DatasetSearchResponse(
            status=APIStatus.OK,
            query=request.query,
            results=[],
            message="동적 공공데이터 검색 기능이 비활성화되어 있습니다.",
            meta=MetaInfo(cache_hit=False, mock_mode=True, elapsed_ms=_elapsed_ms(started_at)),
        )

    try:
        results = search_public_datasets(
            request.query,
            limit=request.limit,
            timeout_seconds=settings.public_api_timeout_seconds,
        )
        return DatasetSearchResponse(
            status=APIStatus.OK,
            query=request.query,
            results=[DatasetSearchItem(**result.__dict__) for result in results],
            meta=MetaInfo(cache_hit=False, mock_mode=False, elapsed_ms=_elapsed_ms(started_at)),
        )
    except Exception as exc:
        logger.warning("dataset_search failed query=%s error=%s", request.query, type(exc).__name__)
        return DatasetSearchResponse(
            status=APIStatus.ERROR,
            query=request.query,
            results=[],
            message="공공데이터셋 검색에 실패했습니다.",
            error_code="DATASET_SEARCH_ERROR",
            meta=MetaInfo(cache_hit=False, mock_mode=False, elapsed_ms=_elapsed_ms(started_at)),
        )


@router.post("/datasets/search", response_model=DatasetSearchResponse)
def search_datasets(request: DatasetSearchRequest) -> DatasetSearchResponse:
    return _search(request)


@router.post("/search", response_model=DatasetSearchResponse)
def search_datasets_alias(request: DatasetSearchRequest) -> DatasetSearchResponse:
    return _search(request)
