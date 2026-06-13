from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import APIStatus, CategoryId


class SearchRequest(BaseModel):
    query: str = Field(..., max_length=200)
    page_url: Optional[str] = None
    source: str = "browser_extension"

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty")
        return stripped

    @field_validator("source")
    @classmethod
    def source_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        return stripped or "browser_extension"


class IntentResult(BaseModel):
    category: CategoryId
    keywords: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_rules: list[str] = Field(default_factory=list)


class IntentResponse(BaseModel):
    status: APIStatus = APIStatus.OK
    intent: IntentResult
