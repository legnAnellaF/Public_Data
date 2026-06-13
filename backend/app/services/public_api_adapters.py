from typing import Any

from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.schemas.public_data import PublicDataRawResult, PublicDataSource
from backend.app.utils.errors import MalformedPublicDataError


def build_query_params(intent: IntentResult, query: str, service_key: str) -> dict[str, str]:
    """Build generic GET parameters without assuming a specific public API contract."""
    params = {"query": query, "category": intent.category.value}
    for key, value in intent.params.items():
        params[key] = str(value)
    if service_key:
        params["serviceKey"] = service_key
    return params


def adapt_external_payload(
    category: CategoryId,
    payload: Any,
    params: dict[str, Any],
    source: PublicDataSource,
) -> PublicDataRawResult:
    """Normalize a configured external API response into the internal raw model.

    This MVP accepts responses that already provide a dictionary under `data`.
    Real public API-specific field mapping should be added here per category.
    """
    if not isinstance(payload, dict):
        raise MalformedPublicDataError()

    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise MalformedPublicDataError()

    return PublicDataRawResult(category=category, params=params, data=data, source=source)
