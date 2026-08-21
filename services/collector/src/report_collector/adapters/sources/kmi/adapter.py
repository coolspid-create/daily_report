import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import urljoin

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

DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}[.-]\d{2}")


class KmiResearchAdapter(SourceAdapter):
    """공개 연구보고서 목록과 공식 문서 뷰어 링크를 연결합니다."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select("tbody.alignC tr") if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError("KMI report list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=_attachments(soup, str(item.detail_url)),
            official_summary=_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("td.tlt a")
    title = link.get_text(" ", strip=True) if link else ""
    href = str(link.get("href", "")) if link else ""
    item_id = re.search(r"[?&]idx=(\d+)", href)
    if not item_id or not title or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(
        source_item_key=item_id.group(1),
        title=title,
        detail_url=HttpUrl(urljoin(str(config.list_url), href)),
        published_at=_date(node.get_text(" ", strip=True)),
    )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group().replace(".", "-")) if match else None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    links = soup.select("a[href*='viewer.do']")
    return [
        Attachment(
            url=HttpUrl(urljoin(base_url, str(link.get("href")))),
            file_name="한국해양수산개발원_연구보고서.pdf",
            declared_type="application/pdf",
        )
        for link in links
    ]


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("table.bbsViewA.wviewT")
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text or None
