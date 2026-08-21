import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

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

DETAIL_PATTERN = re.compile(r"viewCntAdd\('RPT','([^']+)','(/library/10120/contents/\d+)'\)")
DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}[.-]\d{2}")
DETAIL_HOST = "https://library.krihs.re.kr"


class KrihsAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select("li") if (item := _item_from_node(node, self.config))]
        if not items:
            raise SourceParseError("KRIHS report list structure changed")
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
            published_at=_published_at(soup) or item.published_at,
            official_summary=_official_summary(soup),
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


def _item_from_node(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[href*='viewCntAdd']")
    title_node = node.select_one("strong.title")
    href = link.get("href") if link else None
    match = DETAIL_PATTERN.search(href) if isinstance(href, str) else None
    if not title_node or not match:
        return None
    title = title_node.get_text(" ", strip=True)
    if not title or not title_allowed(title, config.filters):
        return None
    published = _date(node.get_text(" ", strip=True))
    return DiscoveredItem(
        source_item_key=match.group(1),
        title=title,
        detail_url=HttpUrl(f"{DETAIL_HOST}{match.group(2)}"),
        published_at=published,
    )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group().replace(".", "-")) if match else None


def _published_at(soup: BeautifulSoup) -> date | None:
    return _date(soup.get_text(" ", strip=True))


def _official_summary(soup: BeautifulSoup) -> str | None:
    section = soup.select_one("#anchor-target-intro section")
    content = section.select_one("div") if section else None
    summary = content.get_text(" ", strip=True) if content else ""
    return re.sub(r"\s+", " ", summary).strip() or None
