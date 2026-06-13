from typing import Any

from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.schemas.public_data import PublicDataRawResult
from backend.app.schemas.widget import ChartData, ChartDataset, WidgetCard, WidgetPayload, WidgetSource, WidgetTable
from backend.app.utils.errors import WidgetTransformError


def _format_value(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _source(raw: PublicDataRawResult) -> WidgetSource:
    return WidgetSource(
        name=raw.source.name,
        url=raw.source.url,
        updated_at=raw.source.updated_at,
        is_mock=raw.source.is_mock,
    )


def _metric_cards(metrics: list[dict[str, Any]]) -> list[WidgetCard]:
    return [
        WidgetCard(
            label=str(item.get("label", "")),
            value=_format_value(item.get("value", "")),
            unit=item.get("unit"),
            description=item.get("description"),
        )
        for item in metrics
    ]


def _metric_table(metrics: list[dict[str, Any]]) -> WidgetTable:
    return WidgetTable(
        columns=["항목", "값", "단위"],
        rows=[
            [str(item.get("label", "")), _format_value(item.get("value", "")), str(item.get("unit", ""))]
            for item in metrics
        ],
    )


def _series_widget(
    title: str,
    summary: str,
    chart_type: str,
    metric_label: str,
    labels: list[str],
    values: list[float],
    unit: str,
    raw: PublicDataRawResult,
) -> WidgetPayload:
    latest_value = values[-1] if values else 0
    return WidgetPayload(
        title=title,
        summary=summary,
        chart=ChartData(
            type=chart_type,
            labels=labels,
            datasets=[ChartDataset(label=metric_label, data=values, unit=unit)],
        ),
        cards=[
            WidgetCard(
                label=metric_label,
                value=_format_value(latest_value),
                unit=unit,
                description="가장 최근 값",
            )
        ],
        table=WidgetTable(
            columns=["기간", metric_label, "단위"],
            rows=[[label, _format_value(value), unit] for label, value in zip(labels, values)],
        ),
        source=_source(raw),
    )


def transform_to_widget(query: str, intent: IntentResult, raw: PublicDataRawResult) -> WidgetPayload:
    """Transform normalized public data into the stable browser-extension widget JSON."""
    try:
        if intent.category == CategoryId.ENVIRONMENT_AIR_QUALITY:
            metrics = list(raw.data["metrics"])
            region = str(raw.data.get("region") or intent.params.get("region") or "서울")
            status = str(raw.data.get("status", "정보 없음"))
            cards = _metric_cards(metrics)
            cards.append(WidgetCard(label="상태", value=status, unit=None, description="대기질 등급"))
            return WidgetPayload(
                title=f"{region} 미세먼지 현황",
                summary="공공데이터 기반 대기질 정보를 시각화했습니다.",
                chart=ChartData(
                    type="bar",
                    labels=[str(item["label"]) for item in metrics],
                    datasets=[
                        ChartDataset(
                            label="농도",
                            data=[float(item["value"]) for item in metrics],
                            unit=str(metrics[0].get("unit", "")) if metrics else "",
                        )
                    ],
                ),
                cards=cards,
                table=_metric_table(metrics),
                source=_source(raw),
            )

        if intent.category == CategoryId.REAL_ESTATE:
            region = str(raw.data.get("region") or intent.params.get("region") or "강남구")
            return _series_widget(
                title=f"{region} 부동산 실거래가 추이",
                summary="공공데이터 기반 부동산 가격 흐름을 시각화했습니다.",
                chart_type="line",
                metric_label=str(raw.data.get("metric_label", "평균 가격")),
                labels=list(raw.data["labels"]),
                values=[float(value) for value in raw.data["values"]],
                unit=str(raw.data.get("unit", "억원")),
                raw=raw,
            )

        if intent.category == CategoryId.TRAFFIC:
            region = str(raw.data.get("region") or intent.params.get("region") or "서울")
            return _series_widget(
                title=f"{region} 교통 혼잡도",
                summary="공공데이터 기반 교통 흐름 정보를 시각화했습니다.",
                chart_type="line",
                metric_label=str(raw.data.get("metric_label", "혼잡도")),
                labels=list(raw.data["labels"]),
                values=[float(value) for value in raw.data["values"]],
                unit=str(raw.data.get("unit", "지수")),
                raw=raw,
            )

        if intent.category == CategoryId.WEATHER:
            metrics = list(raw.data["metrics"])
            region = str(raw.data.get("region") or intent.params.get("region") or "서울")
            return WidgetPayload(
                title=f"{region} 날씨 요약",
                summary="공공데이터 기반 날씨 정보를 시각화했습니다.",
                chart=ChartData(
                    type="bar",
                    labels=[str(item["label"]) for item in metrics],
                    datasets=[
                        ChartDataset(
                            label="날씨 지표",
                            data=[float(item["value"]) for item in metrics],
                            unit="혼합",
                        )
                    ],
                ),
                cards=_metric_cards(metrics),
                table=_metric_table(metrics),
                source=_source(raw),
            )

        if intent.category == CategoryId.ECONOMY:
            return _series_widget(
                title="경제 지표 추이",
                summary="공공데이터 기반 경제 지표를 시각화했습니다.",
                chart_type="line",
                metric_label=str(raw.data.get("metric_label", "경제 지표")),
                labels=list(raw.data["labels"]),
                values=[float(value) for value in raw.data["values"]],
                unit=str(raw.data.get("unit", "지수")),
                raw=raw,
            )
    except Exception as exc:
        raise WidgetTransformError() from exc

    raise WidgetTransformError("지원하지 않는 카테고리는 위젯으로 변환할 수 없습니다.")
