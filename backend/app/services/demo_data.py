from datetime import date
from typing import Any

from backend.app.schemas.common import CategoryId
from backend.app.schemas.public_data import PublicDataRawResult, PublicDataSource


DEMO_SOURCE_NAME = "공공데이터 기반 데모 데이터"


def _source() -> PublicDataSource:
    return PublicDataSource(
        name=DEMO_SOURCE_NAME,
        url=None,
        updated_at=date.today().isoformat(),
        is_mock=True,
    )


def _region(params: dict[str, Any], default: str) -> str:
    value = params.get("region")
    return str(value) if value else default


def get_demo_public_data(category: CategoryId, params: dict[str, Any] | None = None) -> PublicDataRawResult:
    """Return deterministic mock public-data payloads for all supported categories."""
    safe_params = params or {}

    if category == CategoryId.ENVIRONMENT_AIR_QUALITY:
        region = _region(safe_params, "서울")
        data = {
            "region": region,
            "status": "보통",
            "metrics": [
                {"label": "PM10", "value": 42, "unit": "㎍/㎥", "description": "미세먼지"},
                {"label": "PM2.5", "value": 21, "unit": "㎍/㎥", "description": "초미세먼지"},
            ],
        }
    elif category == CategoryId.REAL_ESTATE:
        region = _region(safe_params, "강남구")
        data = {
            "region": region,
            "metric_label": "평균 실거래가",
            "labels": ["4월", "5월", "6월"],
            "values": [18.2, 18.5, 18.7],
            "unit": "억원",
        }
    elif category == CategoryId.TRAFFIC:
        region = _region(safe_params, "서울")
        data = {
            "region": region,
            "metric_label": "혼잡도 지수",
            "labels": ["08시", "12시", "18시"],
            "values": [68, 54, 82],
            "unit": "지수",
        }
    elif category == CategoryId.WEATHER:
        region = _region(safe_params, "서울")
        data = {
            "region": region,
            "metrics": [
                {"label": "기온", "value": 27.4, "unit": "℃", "description": "현재 기온"},
                {"label": "강수량", "value": 0, "unit": "mm", "description": "일 강수량"},
                {"label": "습도", "value": 61, "unit": "%", "description": "현재 습도"},
            ],
        }
    elif category == CategoryId.ECONOMY:
        data = {
            "region": "전국",
            "metric_label": "소비자물가지수",
            "labels": ["4월", "5월", "6월"],
            "values": [112.6, 113.0, 113.4],
            "unit": "지수",
        }
    else:
        data = {}

    return PublicDataRawResult(
        category=category,
        params=safe_params,
        data=data,
        source=_source(),
    )
