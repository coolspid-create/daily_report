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

_NUMBER = re.compile(r'BOUBUF02N00\((?:&quot;|["\'])(\d+)(?:&quot;|["\']),(?:&quot;|["\'])(\d+)')
_DATE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")


class KdbFutureStrategyAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None) -> None:
        if browser is None:
            raise ValueError("KDB source requires browser rendering")
        self.config, self.browser = config, browser

    async def _html(self) -> str:
        return await self.browser.render(
            str(self.config.list_url), self.config.browser.wait_for, self.config.browser.timeout_ms
        )

    def _items(self, html: str) -> list[DiscoveredItem]:
        items = [_item(row, self.config) for row in BeautifulSoup(html, "html.parser").select("#tableList tbody tr")]
        result = [item for item in items if item]
        if not result:
            raise SourceParseError("KDB report list structure changed")
        return result

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._items(await self._html()):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        row = _matching_row(await self._html(), item.source_item_key)
        attachment = _attachment(row, str(self.config.list_url))
        return SourceDocument(
            source_item_key=item.source_item_key, title=item.title, institution=self.config.name,
            detail_url=item.detail_url, published_at=item.published_at,
            attachments=[attachment] if attachment else [], rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._items(await self._html()))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(row: Tag, config: SourceConfig) -> DiscoveredItem | None:
    title_link = row.select_one("td.al a.links")
    match = _NUMBER.search(str(title_link.get("onclick", ""))) if title_link else None
    title = title_link.get_text(" ", strip=True) if title_link else ""
    if not match or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(
        source_item_key=match.group(2), title=title, detail_url=config.list_url,
        published_at=_date(row.get_text(" ", strip=True)),
    )


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None


def _matching_row(html: str, key: str) -> Tag | None:
    for row in BeautifulSoup(html, "html.parser").select("#tableList tbody tr"):
        if f'"{key}"' in str(row) or f"&quot;{key}&quot;" in str(row):
            return row
    return None


def _attachment(row: Tag | None, base_url: str) -> Attachment | None:
    link = row.select_one("a.bbsBtn.pdf[href]") if row else None
    href = link.get("href") if isinstance(link, Tag) else None
    if not isinstance(href, str):
        return None
    title = link.get("title") if isinstance(link, Tag) else None
    file_name = title if isinstance(title, str) else "KDB-report.pdf"
    return Attachment(url=HttpUrl(urljoin(base_url, href)), file_name=file_name)
