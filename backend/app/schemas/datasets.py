from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import APIStatus, MetaInfo


class DatasetSearchRequest(BaseModel):
    query: str = Field(..., max_length=200)
    page_url: Optional[str] = None
    source: str = "browser_extension"
    limit: int = Field(default=5, ge=1, le=10)

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


class DatasetSearchItem(BaseModel):
    title: str
    provider: str = ""
    link: str
    description: Optional[str] = None
    summary: Optional[str] = None
    source: str = "data.go.kr"


class DatasetSearchResponse(BaseModel):
    status: APIStatus = APIStatus.OK
    query: str
    results: list[DatasetSearchItem] = Field(default_factory=list)
    meta: MetaInfo
    message: Optional[str] = None
    error_code: Optional[str] = None
