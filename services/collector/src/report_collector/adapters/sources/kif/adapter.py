import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl
from report_collector.adapters.base import SourceAdapter
from report_collector.domain.errors import SourceParseError
from report_collector.domain.models import (
    Attachment,
    DiscoveredItem,
    SourceConfig,
    SourceDocument,
    SourceHealthResult,
)
from report_collector.providers.browser.base import BrowserRenderer
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.services.source_filter_service import title_allowed

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
DOWNLOAD_PATTERN = re.compile(
    r"execDownload\(\s*'[^']*'\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']+)'\s*,\s*'[^']*'\s*,\s*(\d+)\s*\)"
)


class KifRenderedAdapter(SourceAdapter):
    """공개 페이지를 정상 브라우저 렌더링한 결과만 파싱한다."""

    def __init__(
        self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None
    ) -> None:
        if browser is None:
            raise ValueError("KIF adapter requires a browser renderer")
        self.config = config
        self.browser = browser
        self._session = None

    async def _render(self, url: str, wait_for: str | None, referer: str | None = None) -> str:
        if self._session is not None:
            return await self._session.render(url, wait_for, self.config.browser.timeout_ms, referer)
        return await self.browser.render(url, wait_for, self.config.browser.timeout_ms)

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredItem] = []
        for node in soup.select("#ContentsList .info, #maincontent .info"):
            link = node.select_one("a.title[href*='pub_detail']")
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            key = parse_qs(urlparse(str(link["href"])).query).get("cno", [""])[0]
            if not key or not title_allowed(title, self.config.filters):
                continue
            results.append(
                DiscoveredItem(
                    source_item_key=key,
                    title=title,
                    detail_url=HttpUrl(urljoin(str(self.config.list_url), str(link["href"]))),
                    published_at=_date(node.get_text(" ", strip=True)),
                )
            )
        if not results:
            raise SourceParseError("KIF publication list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        opener = getattr(self.browser, "open_session", None)
        self._session = await opener() if callable(opener) else None
        try:
            html = await self._render(str(self.config.list_url), self.config.browser.wait_for)
            for item in self._parse_list(html):
                if item.source_item_key == cursor:
                    break
                yield item
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self._render(str(item.detail_url), ".info_detail", str(self.config.list_url))
        soup = BeautifulSoup(html, "html.parser")
        detail = soup.select_one(f"#detail_{item.source_item_key}.info_detail")
        if detail is None:
            detail = soup.select_one(f"#info_{item.source_item_key} .info_detail")
        summary = detail.select_one(".tab_content.current, .summary, .info_summary") if detail else None
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=_attachments(detail, str(item.detail_url)),
            official_summary=_text(summary),
            rights_status=self.config.rights_default,
        )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self._render(str(self.config.list_url), self.config.browser.wait_for)
            count = len(self._parse_list(html))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group()) if match else None


def _text(node: Tag | None) -> str | None:
    if node is None:
        return None
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
    return text[:3000] or None


def _attachments(detail: Tag | None, base_url: str) -> list[Attachment]:
    if detail is None:
        return []
    link = detail.select_one("button.btn_download[onclick*='execDownload']")
    if link is None:
        return []
    match = DOWNLOAD_PATTERN.search(str(link.get("onclick", "")))
    if match is None:
        return []
    mid, vid, cno, file_code, file_index = match.groups()
    url = f"{urljoin(base_url, '/kif4/publication/viewer')}?mid={mid}&vid={vid}&cno={cno}&fcd={file_code}&ft={file_index}"
    name = str(link.get("title", "")).strip() or f"kif-{cno}.pdf"
    return [Attachment(url=HttpUrl(url), file_name=name, declared_type="application/pdf")]
