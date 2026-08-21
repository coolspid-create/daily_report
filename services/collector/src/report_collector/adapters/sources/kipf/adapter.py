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

DETAIL_KEY_PATTERN = re.compile(r"fn_search_detail\('(\d+)'\)")
DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}")
DETAIL_ACTION = "/kor/Publication/KipfReport/kiPublish/CA/view.do"


class KipfAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None = None
    ) -> None:
        if browser is None:
            raise ValueError("KIPF requires a browser renderer for its public POST form")
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
        await self.browser.submit_form(
            str(self.config.list_url),
            "form#searchForm",
            {"serialNo": item.source_item_key},
            DETAIL_ACTION,
            ".detail-article",
            self.config.browser.timeout_ms,
        )
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=self.config.list_url,
            published_at=item.published_at,
            official_summary=None,
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
    items = [item for link in soup.select("a.link") if (item := _item(link, config))]
    if not items:
        raise SourceParseError("KIPF report list structure changed")
    return items


def _item(link: Tag, config: SourceConfig) -> DiscoveredItem | None:
    onclick = link.get("onclick")
    match = DETAIL_KEY_PATTERN.search(onclick) if isinstance(onclick, str) else None
    title = _text(link.select_one("strong.tit"))
    if not match or not title or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(
        source_item_key=match.group(1),
        title=title,
        detail_url=config.list_url,
        published_at=_date(_text(link)),
    )


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(f"{match.group().replace('.', '-')}-01") if match else None


def _text(node: Tag | None) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True) if node else "").strip()
