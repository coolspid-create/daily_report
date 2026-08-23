import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl
from report_collector.adapters.base import SourceAdapter
from report_collector.domain.errors import SourceParseError
from report_collector.domain.models import (
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


class CreditRatingAdapter(SourceAdapter):
    """3대 신용평가사(NICE, 한국기업평가, 한국신용평가)의 공개 리서치 목록 및 상세 웹 링크를 LINK_ONLY로 안전하게 수집합니다."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        selector = (
            self.config.selectors.list_item
            if self.config.selectors
            else "tbody tr, .research li, ul.list li"
        )
        items: list[DiscoveredItem] = []
        for node in soup.select(selector):
            item = _parse_item(node, self.config)
            if item:
                items.append(item)
        if not items:
            raise SourceParseError(f"{self.config.name} research list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.http.fetch_text(str(self.config.list_url))
        for item in self._parse_list(html):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        # 신용평가사는 공개 상세/목록 웹페이지로의 직접 링크(LINK_ONLY)를 제공하며 보호된 파일 다운로드는 직접 호출하지 않습니다.
        summary: str | None = None
        published = item.published_at
        try:
            html = await self.http.fetch_text(str(item.detail_url))
            soup = BeautifulSoup(html, "html.parser")
            summary_node = soup.select_one(".view-content, .detail_cont, .article_body, .content")
            if summary_node:
                summary = re.sub(r"\s+", " ", summary_node.get_text(" ", strip=True)).strip()[:3000]
            if not published:
                published = _extract_date(soup.get_text(" ", strip=True))
        except Exception:
            # 상세 페이지가 단독 조회가 안 되는 프레임 구조일 경우 목록에서 추출한 정보 우선 사용
            pass

        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=published,
            attachments=[],
            official_summary=summary,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self.http.fetch_text(str(self.config.list_url))
            count = len(self._parse_list(html))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _parse_item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[href]") or node.select_one("a")
    if not link:
        return None
    title = link.get_text(" ", strip=True)
    if not title or not title_allowed(title, config.filters):
        return None
    href = str(link.get("href", "")).strip()
    key = _extract_key(href, node)
    published = _extract_date(node.get_text(" ", strip=True))

    detail_url = (
        urljoin(str(config.list_url), href)
        if href and not href.startswith("javascript:")
        else str(config.list_url)
    )

    return DiscoveredItem(
        source_item_key=key,
        title=title,
        detail_url=HttpUrl(detail_url),
        published_at=published,
    )


def _extract_key(href: str, node: Tag) -> str:
    # URL 파라미터나 숫자 ID 추출
    match = re.search(r"(?:seq|id|no|articleId|reportId)=(\d+)", href, re.IGNORECASE)
    if match:
        return match.group(1)
    js_match = re.search(r"['\"](\d+)['\"]", href)
    if js_match:
        return js_match.group(1)
    # 텍스트 기반 해시 또는 fallback key
    title = node.select_one("a")
    return str(hash(title.get_text(strip=True) if title else href))


def _extract_date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    if not match:
        return None
    try:
        return date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError:
        return None
