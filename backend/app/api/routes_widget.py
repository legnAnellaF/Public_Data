import logging
import time
from typing import Any

from fastapi import APIRouter

from backend.app.schemas.common import APIStatus, CategoryId, MetaInfo
from backend.app.schemas.intent import SearchRequest
from backend.app.schemas.widget import WidgetResponse
from backend.app.services.cache import build_cache_key, widget_response_cache
from backend.app.services.intent_rules import analyze_intent
from backend.app.services.public_api_client import PublicApiClient
from backend.app.services.widget_transformer import transform_to_widget
from backend.app.utils.errors import PublicDataAppError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["widget"])


def _elapsed_ms(started_at: float) -> int:
    return max(0, int((time.perf_counter() - started_at) * 1000))


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _cached_response(response: WidgetResponse, elapsed_ms: int) -> WidgetResponse:
    payload = _dump_model(response)
    payload["meta"]["cache_hit"] = True
    payload["meta"]["elapsed_ms"] = elapsed_ms
    return WidgetResponse(**payload)


@router.post("/widget", response_model=WidgetResponse)
def widget(request: SearchRequest) -> WidgetResponse:
    started_at = time.perf_counter()
    intent = analyze_intent(request.query)

    if intent.category == CategoryId.UNKNOWN:
        logger.info("widget unsupported query=%s category=unknown", request.query)
        return WidgetResponse(
            status=APIStatus.UNSUPPORTED,
            query=request.query,
            message="현재 지원하지 않는 검색어입니다.",
            intent=intent,
            widget=None,
            meta=MetaInfo(cache_hit=False, mock_mode=True, elapsed_ms=_elapsed_ms(started_at)),
        )

    cache_key = build_cache_key(intent.category.value, intent.params, request.query)
    cached = widget_response_cache.get(cache_key)
    if cached is not None:
        logger.info("widget cache_hit=true query=%s category=%s", request.query, intent.category.value)
        return _cached_response(cached, _elapsed_ms(started_at))

    try:
        logger.info("widget cache_hit=false query=%s category=%s", request.query, intent.category.value)
        fetch_result = PublicApiClient().fetch(intent, request.query)
        widget_payload = transform_to_widget(request.query, intent, fetch_result.raw)
        response = WidgetResponse(
            status=APIStatus.OK,
            query=request.query,
            intent=intent,
            widget=widget_payload,
            meta=MetaInfo(
                cache_hit=False,
                mock_mode=fetch_result.raw.source.is_mock or fetch_result.used_mock,
                elapsed_ms=_elapsed_ms(started_at),
            ),
        )
        widget_response_cache.set(cache_key, response)
        return response
    except PublicDataAppError as exc:
        logger.warning(
            "widget handled_error query=%s category=%s error_code=%s",
            request.query,
            intent.category.value,
            exc.error_code,
        )
        return WidgetResponse(
            status=APIStatus.ERROR,
            query=request.query,
            message=exc.message,
            error_code=exc.error_code,
            intent=intent,
            widget=None,
            meta=MetaInfo(cache_hit=False, mock_mode=False, elapsed_ms=_elapsed_ms(started_at)),
        )
