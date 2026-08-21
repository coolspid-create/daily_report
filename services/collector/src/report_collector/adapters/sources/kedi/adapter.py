import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

from bs4 import BeautifulSoup, Tag
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

DETAIL_KEY_PATTERN = re.compile(r"selectPubFormFn\('(\d+)'\)")
DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}[.-]\d{2}")
DETAIL_ACTION = "/khome/main/research/selectPubForm.do"


class KediAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None = None
    ) -> None:
        if browser is None:
            raise ValueError("KEDI requires a browser renderer for its public POST form")
        self.browser = browser
        self.config = config

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.browser.render(
            str(self.config.list_url), self.config.browser.wait_for, self.config.browser.timeout_ms
        )
        for item in _items(html, self.config):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.browser.submit_form(
            str(self.config.list_url),
            "form#listPubForm",
            {"plNum0": item.source_item_key},
            DETAIL_ACTION,
            "#report .reportSummary .reportCont",
            self.config.browser.timeout_ms,
        )
        soup = BeautifulSoup(html, "html.parser")
        summary = _text(soup.select_one("#report .reportSummary .reportCont"))
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=self.config.list_url,
            published_at=item.published_at,
            official_summary=summary or None,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(_items(await self.browser.render(str(self.config.list_url), None, 30000), self.config))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _items(html: str, config: SourceConfig) -> list[DiscoveredItem]:
    soup = BeautifulSoup(html, "html.parser")
    items = [item for row in soup.select("tr") if (item := _item(row, config))]
    if not items:
        raise SourceParseError("KEDI report list structure changed")
    return items


def _item(row: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = row.select_one("a[onclick*='selectPubFormFn']")
    onclick = link.get("onclick") if link else None
    match = DETAIL_KEY_PATTERN.search(onclick) if isinstance(onclick, str) else None
    title = _text(link)
    if not match or not title or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(
        source_item_key=match.group(1),
        title=title,
        detail_url=config.list_url,
        published_at=_date(_text(row)),
    )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group().replace(".", "-")) if match else None


def _text(node: Tag | None) -> str:
    value = node.get_text(" ", strip=True) if node else ""
    return re.sub(r"\s+", " ", value)[:3000]
