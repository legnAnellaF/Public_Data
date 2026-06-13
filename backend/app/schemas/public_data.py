from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.schemas.common import CategoryId


class PublicDataSource(BaseModel):
    name: str
    url: Optional[str] = None
    updated_at: str
    is_mock: bool = True


class PublicDataRawResult(BaseModel):
    category: CategoryId
    params: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)
    source: PublicDataSource
