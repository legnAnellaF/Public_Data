from typing import Any, Mapping

from backend.app.schemas.intent import IntentResult
from backend.app.schemas.widget import ChartData, ChartDataset, WidgetCard, WidgetPayload, WidgetSource, WidgetTable
from backend.app.utils.errors import WidgetTransformError


def _chart_type(value: Any) -> str:
    normalized = str(value or "bar").lower()
    if normalized == "line":
        return "line"
    return "bar"


def _format_value(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _numeric_list(values: Any, length: int) -> list[float]:
    source = values if isinstance(values, list) else []
    result: list[float] = []
    for index in range(length):
        try:
            result.append(float(source[index]))
        except Exception:
            result.append(0.0)
    return result


def _source(source_payload: Any, target_link: str | None) -> WidgetSource:
    if isinstance(source_payload, Mapping):
        return WidgetSource(
            name=str(source_payload.get("name") or "공공데이터포털 실시간 다운로드"),
            url=str(source_payload.get("url") or target_link) if (source_payload.get("url") or target_link) else None,
            updated_at=str(source_payload.get("updated_at") or "dynamic"),
            is_mock=bool(source_payload.get("is_mock", False)),
        )
    return WidgetSource(
        name=str(source_payload or "공공데이터포털 실시간 다운로드"),
        url=target_link,
        updated_at="dynamic",
        is_mock=False,
    )


def adapt_dynamic_widget_data(
    query: str,
    intent: IntentResult,
    dynamic_payload: Mapping[str, Any],
    target_link: str | None = None,
) -> WidgetPayload:
    chart_payload = dynamic_payload.get("chart")
    if not isinstance(chart_payload, Mapping):
        raise WidgetTransformError("동적 데이터에 차트 정보가 없습니다.")

    labels = [str(label) for label in chart_payload.get("labels", []) if str(label)]
    raw_datasets = chart_payload.get("datasets")
    if not labels or not isinstance(raw_datasets, list):
        raise WidgetTransformError("동적 차트 데이터 형식이 올바르지 않습니다.")

    datasets: list[ChartDataset] = []
    for index, dataset in enumerate(raw_datasets):
        if not isinstance(dataset, Mapping):
            continue
        values = _numeric_list(dataset.get("data"), len(labels))
        if not any(values):
            continue
        datasets.append(
            ChartDataset(
                label=str(dataset.get("label") or f"데이터 {index + 1}"),
                data=values,
                unit=str(dataset.get("unit") or ""),
            )
        )

    if not datasets:
        raise WidgetTransformError("동적 데이터에서 수치형 지표를 찾지 못했습니다.")

    primary = datasets[0]
    total = sum(primary.data)
    average = total / len(primary.data) if primary.data else 0.0
    maximum = max(primary.data) if primary.data else 0.0
    cards = [
        WidgetCard(label=f"{primary.label} 합계", value=_format_value(total), unit=primary.unit, description="동적 데이터 합계"),
        WidgetCard(label=f"{primary.label} 평균", value=_format_value(average), unit=primary.unit, description="동적 데이터 평균"),
        WidgetCard(label=f"{primary.label} 최대", value=_format_value(maximum), unit=primary.unit, description="동적 데이터 최댓값"),
    ]

    columns = ["항목"] + [dataset.label for dataset in datasets]
    rows = []
    for row_index, label in enumerate(labels[:20]):
        rows.append([label] + [_format_value(dataset.data[row_index]) for dataset in datasets])

    return WidgetPayload(
        title=str(dynamic_payload.get("title") or f"{query} 공공데이터 분석"),
        summary=str(dynamic_payload.get("summary") or "공공데이터포털 파일 데이터를 분석했습니다."),
        chart=ChartData(
            type=_chart_type(chart_payload.get("type")),
            labels=labels,
            datasets=datasets,
        ),
        cards=cards,
        table=WidgetTable(columns=columns, rows=rows),
        source=_source(dynamic_payload.get("source"), target_link),
    )
