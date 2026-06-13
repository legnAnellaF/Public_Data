from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class APIStatus(str, Enum):
    """Allowed top-level API status values."""

    OK = "ok"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class CategoryId(str, Enum):
    """Supported public-data categories."""

    ENVIRONMENT_AIR_QUALITY = "environment_air_quality"
    REAL_ESTATE = "real_estate"
    TRAFFIC = "traffic"
    WEATHER = "weather"
    ECONOMY = "economy"
    UNKNOWN = "unknown"


class MetaInfo(BaseModel):
    cache_hit: bool = False
    mock_mode: bool = True
    elapsed_ms: int = Field(default=0, ge=0)


class ErrorResponse(BaseModel):
    status: APIStatus = APIStatus.ERROR
    query: Optional[str] = None
    message: str
    error_code: str
    detail: Optional[Any] = None
