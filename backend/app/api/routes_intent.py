import logging

from fastapi import APIRouter

from backend.app.schemas.common import APIStatus
from backend.app.schemas.intent import IntentResponse, SearchRequest
from backend.app.services.intent_rules import analyze_intent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["intent"])


@router.post("/intent", response_model=IntentResponse)
def intent(request: SearchRequest) -> IntentResponse:
    result = analyze_intent(request.query)
    logger.info(
        "intent query=%s category=%s confidence=%.2f",
        request.query,
        result.category.value,
        result.confidence,
    )
    return IntentResponse(status=APIStatus.OK, intent=result)
