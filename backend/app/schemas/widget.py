from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.common import APIStatus, MetaInfo
from backend.app.schemas.intent import IntentResult


class ChartDataset(BaseModel):
    label: str
    data: list[float]
    unit: str = ""


class ChartData(BaseModel):
    type: str = Field(..., pattern="^(bar|line|card|table)$")
    labels: list[str]
    datasets: list[ChartDataset]


class WidgetCard(BaseModel):
    label: str
    value: str
    unit: Optional[str] = None
    description: Optional[str] = None


class WidgetTable(BaseModel):
    columns: list[str]
    rows: list[list[str]]


class WidgetSource(BaseModel):
    name: str
    url: Optional[str] = None
    updated_at: str
    is_mock: bool = True


class WidgetPayload(BaseModel):
    title: str
    summary: str
    chart: ChartData
    cards: list[WidgetCard]
    table: WidgetTable
    source: WidgetSource


class WidgetResponse(BaseModel):
    status: APIStatus
    query: str
    intent: IntentResult
    widget: Optional[WidgetPayload] = None
    meta: MetaInfo
    message: Optional[str] = None
    error_code: Optional[str] = None
