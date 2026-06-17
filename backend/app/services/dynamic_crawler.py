import logging
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DOWNLOAD_SELECTOR = (
    "a:has-text('다운로드'), "
    "a.button:has-text('다운로드'), "
    "a[href*='fileDownload'], "
    "a:has-text('CSV'), "
    "a:has-text('Excel'), "
    "a:has-text('엑셀')"
)


def get_dynamic_download_dir(base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir) if base_dir is not None else Path(tempfile.gettempdir()) / "public_data_widget"
    download_dir = base / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def _safe_filename(filename: str, fallback: str) -> str:
    name = Path(filename or fallback).name
    safe = re.sub(r"[^0-9A-Za-z가-힣._ -]+", "_", name).strip(" .")
    return safe or fallback


def _is_allowed_target_link(target_link: str) -> bool:
    parsed = urlparse(target_link)
    return parsed.scheme in {"http", "https"} and parsed.netloc.endswith("data.go.kr")


def crawl_public_data_file(
    keyword: str,
    target_link: str | None = None,
    download_dir: str | Path | None = None,
    timeout_ms: int = 15000,
) -> str | None:
    if not target_link:
        return None
    if not _is_allowed_target_link(target_link):
        logger.warning("dynamic_crawler rejected target_link=%s", target_link)
        return None

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.info("dynamic_crawler playwright_unavailable error=%s", type(exc).__name__)
        return None

    target_dir = get_dynamic_download_dir(download_dir)
    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.goto(target_link, timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=timeout_ms)

            download_button = page.locator(DOWNLOAD_SELECTOR).first
            download_button.wait_for(state="visible", timeout=5000)

            with page.expect_download(timeout=timeout_ms) as download_info:
                download_button.click()

            download = download_info.value
            fallback_name = f"{keyword or 'public_data'}_download"
            final_path = target_dir / _safe_filename(download.suggested_filename, fallback_name)
            download.save_as(str(final_path))
            return str(final_path)
    except Exception as exc:  # pragma: no cover - exercised manually with browser/runtime
        logger.warning("dynamic_crawler failed target_link=%s error=%s", target_link, type(exc).__name__)
        return None
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                logger.debug("dynamic_crawler browser_close_failed", exc_info=True)


def crawl_public_data_csv(keyword: str, target_link: str | None = None) -> str | None:
    return crawl_public_data_file(keyword, target_link)
