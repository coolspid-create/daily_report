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

DATE_PATTERN = re.compile(
    r"(?P<year>\d{4})\s*[./-]\s*(?P<month>\d{1,2})\s*[./-]\s*(?P<day>\d{1,2})"
)
YEAR_PATTERN = re.compile(r"(?P<year>\d{4})\s*(?:년)?")


class KihasaAdapter(SourceAdapter):
    """한국보건사회연구원 2-Step 어댑터: 목록에서 후보를 발견하고 상세 페이지에서 정밀 일자(YYYY-MM-DD)를 파싱합니다."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, browser: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http
        self.browser = browser

    async def _fetch_html(self, url: str) -> str:
        if self.browser:
            return await self.browser.render(
                url, self.config.browser.wait_for, self.config.browser.timeout_ms
            )
        return await self.http.fetch_text(url)

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[DiscoveredItem] = []
        for node in soup.select(".rpt-thumb-li, li.report-item, .board-list li"):
            item = _parse_item(node, self.config)
            if item:
                items.append(item)
        if not items:
            raise SourceParseError("KIHASA report list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self._fetch_html(str(self.config.list_url))
        for item in self._parse_list(html):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self._fetch_html(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")

        # 상세 페이지에서 정밀 발행일자 파싱
        detail_date = _extract_precise_date(soup)
        published_at = detail_date or item.published_at

        # 공식 요약 추출
        summary_node = soup.select_one(".report-summary, .view-cont, .content, main p")
        summary = (
            re.sub(r"\s+", " ", summary_node.get_text(" ", strip=True)).strip()[:3000]
            if summary_node
            else None
        )

        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=published_at,
            attachments=[],
            official_summary=summary,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self._fetch_html(str(self.config.list_url))
            count = len(self._parse_list(html))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _parse_item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one(".title a[href*='view'], a[href*='view']") or node.select_one("a")
    if not link:
        return None
    title = link.get_text(" ", strip=True)
    if not title or not title_allowed(title, config.filters):
        return None
    href = str(link.get("href", ""))
    detail_url = urljoin(str(config.list_url), href)
    params = parse_qs(urlparse(detail_url).query)
    seq = params.get("seq", [""])[0] or str(hash(title))

    # 목록의 일자가 완전한 YYYY-MM-DD인 경우만 추출, 연도만 있는 경우 None으로 반환하여 fetch_detail에서 추출하도록 유도
    list_date = _extract_precise_date(node)

    return DiscoveredItem(
        source_item_key=seq,
        title=title,
        detail_url=HttpUrl(detail_url),
        published_at=list_date,
    )


def _extract_precise_date(node_or_soup: Tag | BeautifulSoup) -> date | None:
    text = node_or_soup.get_text(" ", strip=True)
    match = DATE_PATTERN.search(text)
    if match:
        try:
            return date(
                int(match.group("year")), int(match.group("month")), int(match.group("day"))
            )
        except ValueError:
            return None
    return None
