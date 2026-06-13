import logging
from dataclasses import dataclass

import httpx

from backend.app.config import Settings, get_settings
from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.schemas.public_data import PublicDataRawResult, PublicDataSource
from backend.app.services.demo_data import get_demo_public_data
from backend.app.services.public_api_adapters import adapt_external_payload, build_query_params
from backend.app.utils.errors import PublicApiError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublicApiFetchResult:
    raw: PublicDataRawResult
    used_mock: bool
    fallback_reason: str | None = None


class PublicApiClient:
    """Fetch public data through mock-first or configured HTTP GET integrations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def fetch(self, intent: IntentResult, query: str, allow_fallback: bool = True) -> PublicApiFetchResult:
        category = intent.category
        if category == CategoryId.UNKNOWN:
            raise PublicApiError("지원하지 않는 검색어입니다.")

        if self.settings.mock_public_api:
            logger.info("public_api mock_mode=true category=%s", category.value)
            return PublicApiFetchResult(raw=get_demo_public_data(category, intent.params), used_mock=True)

        base_url = self.settings.base_url_for_category(category.value)
        if not base_url:
            return self._fallback(category, intent.params, "base_url_missing", allow_fallback)
        if not self.settings.public_data_service_key:
            return self._fallback(category, intent.params, "service_key_missing", allow_fallback)

        try:
            logger.info("public_api external_call category=%s base_url_configured=true", category.value)
            with httpx.Client(timeout=self.settings.public_api_timeout_seconds) as client:
                response = client.get(
                    base_url,
                    params=build_query_params(intent, query, self.settings.public_data_service_key),
                )
                response.raise_for_status()
                payload = response.json()
            source = PublicDataSource(
                name=f"Configured public API: {category.value}",
                url=base_url,
                updated_at="external",
                is_mock=False,
            )
            raw = adapt_external_payload(category, payload, intent.params, source)
            return PublicApiFetchResult(raw=raw, used_mock=False)
        except Exception as exc:
            logger.warning("public_api external_call_failed category=%s error=%s", category.value, type(exc).__name__)
            return self._fallback(category, intent.params, "external_call_failed", allow_fallback)

    def _fallback(
        self,
        category: CategoryId,
        params: dict[str, object],
        reason: str,
        allow_fallback: bool,
    ) -> PublicApiFetchResult:
        if not allow_fallback:
            raise PublicApiError()
        logger.info("public_api fallback_to_mock category=%s reason=%s", category.value, reason)
        return PublicApiFetchResult(
            raw=get_demo_public_data(category, params),
            used_mock=True,
            fallback_reason=reason,
        )
