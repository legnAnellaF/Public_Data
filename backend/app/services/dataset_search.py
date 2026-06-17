import logging
import re
from dataclasses import dataclass
from collections.abc import Callable
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin

import httpx

from backend.app.services.dynamic_scraper import extract_keywords

logger = logging.getLogger(__name__)

DATA_GO_KR_BASE_URL = "https://www.data.go.kr"
DATA_GO_KR_SEARCH_PATH = "/tcs/dss/selectDataSetList.do"


@dataclass(frozen=True)
class DatasetSearchResult:
    title: str
    provider: str
    link: str
    description: str | None = None
    summary: str | None = None
    source: str = "data.go.kr"


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
    for key, value in attrs:
        if key == "class" and value:
            return set(value.split())
    return set()


def _attr(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    for key, value in attrs:
        if key == name:
            return value
    return None


def _cleanup_provider(provider: str) -> str:
    provider = _clean_text(provider)
    provider = re.sub(r"^(제공기관|제공처|기관명)\s*[:：]?\s*", "", provider)
    provider = re.split(r"\s+(수정일|조회수|다운로드|키워드)\s*", provider)[0].strip()
    return provider[:100]


class _DataGoKrDatasetParser(HTMLParser):
    def __init__(self, limit: int) -> None:
        super().__init__(convert_charrefs=True)
        self.limit = limit
        self.items: list[DatasetSearchResult] = []
        self._result_depth = 0
        self._li_depth = 0
        self._current: dict[str, object] | None = None
        self._capture_stack: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = _classes(attrs)
        if self._result_depth > 0:
            self._result_depth += 1
        elif "result-list" in classes:
            self._result_depth = 1

        if self._current is not None:
            self._li_depth += 1
        elif self._result_depth > 0 and tag == "li":
            self._current = {
                "title_parts": [],
                "provider_parts": [],
                "description_parts": [],
                "all_parts": [],
                "link": "",
            }
            self._li_depth = 1

        if self._current is None:
            return

        if tag == "a" and not self._current.get("link"):
            href = _attr(attrs, "href")
            if href:
                self._current["link"] = urljoin(DATA_GO_KR_BASE_URL, href)

        field = self._field_for(tag, classes)
        if field:
            self._capture_stack.append((tag, field))

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        text = _clean_text(data)
        if not text:
            return
        self._current["all_parts"].append(text)  # type: ignore[union-attr]
        if self._capture_stack:
            _, field = self._capture_stack[-1]
            self._current[f"{field}_parts"].append(text)  # type: ignore[union-attr]

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None:
            while self._capture_stack and self._capture_stack[-1][0] == tag:
                self._capture_stack.pop()
            self._li_depth -= 1
            if self._li_depth <= 0:
                self._finish_item()

        if self._result_depth > 0:
            self._result_depth -= 1

    def _field_for(self, tag: str, classes: set[str]) -> str | None:
        if "title" in classes or tag == "dt":
            return "title"
        if "info-data" in classes:
            return "provider"
        if tag == "a" and self._current is not None and not self._current.get("title_parts"):
            return "title"
        if tag == "dd" or classes.intersection({"desc", "description", "summary", "ellipsis"}):
            return "description"
        return None

    def _finish_item(self) -> None:
        if self._current is None:
            return
        title = _clean_text(" ".join(self._current["title_parts"]))  # type: ignore[index]
        provider = _cleanup_provider(" ".join(self._current["provider_parts"]))  # type: ignore[index]
        description = _clean_text(" ".join(self._current["description_parts"]))  # type: ignore[index]
        link = str(self._current.get("link") or "")

        if not title:
            all_text = _clean_text(" ".join(self._current["all_parts"]))  # type: ignore[index]
            title = all_text[:120]
        if description == title:
            description = ""

        if title and link and len(self.items) < self.limit:
            self.items.append(
                DatasetSearchResult(
                    title=title,
                    provider=provider or "공공데이터포털",
                    link=link,
                    description=description or None,
                    summary=description or None,
                )
            )

        self._current = None
        self._capture_stack.clear()
        self._li_depth = 0


def _main_keyword(query: str) -> str:
    keywords = extract_keywords(query)
    return " ".join(keywords[:2]) if keywords else query.strip()


def build_data_go_kr_search_url(query: str) -> str:
    keyword = _main_keyword(query)
    params = urlencode(
        {
            "dType": "FILE",
            "keyword": keyword,
            "detailKeyword": keyword,
            "sort": "reqCo",
        }
    )
    return f"{DATA_GO_KR_BASE_URL}{DATA_GO_KR_SEARCH_PATH}?{params}"


def parse_data_go_kr_dataset_html(html: str, limit: int = 5) -> list[DatasetSearchResult]:
    parser = _DataGoKrDatasetParser(limit=limit)
    parser.feed(html)
    return parser.items[:limit]


def _fetch_dataset_html(url: str, timeout_seconds: int) -> str:
    headers = {"User-Agent": "Mozilla/5.0 PublicDataWidget/0.1"}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def search_public_datasets(
    query: str,
    limit: int = 5,
    timeout_seconds: int = 5,
    fetch_html: Callable[[str], str] | None = None,
) -> list[DatasetSearchResult]:
    url = build_data_go_kr_search_url(query)
    html = fetch_html(url) if fetch_html is not None else _fetch_dataset_html(url, timeout_seconds)
    results = parse_data_go_kr_dataset_html(html, limit=limit)
    logger.info("dataset_search query=%s results=%d", query, len(results))
    return results
