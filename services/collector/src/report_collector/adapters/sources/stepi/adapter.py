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

REPORT_PATTERN = re.compile(r"reportView\((\d+),'([A-Z0-9]+)'\)")
DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}[.-]\d{2}")
DETAIL_URL = "https://www.stepi.re.kr/site/stepiko/report/View.do?cateCont={category}&reIdx={report_id}"


class StepiAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, browser: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http
        self.browser = browser

    async def _page(self, url: str) -> str:
        if self.browser is None:
            return await self.http.fetch_text(url)
        return await self.browser.render(url, self.config.browser.wait_for, self.config.browser.timeout_ms)

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select("li") if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError("STEPI report list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self._page(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self._page(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_published_at(soup) or item.published_at,
            official_summary=_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self._page(str(self.config.list_url))))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = (
        node.select_one("a[href*='reportView']")
        or node.select_one("a[onclick*='reportView']")
        or node.select_one("a[href*='reIdx']")
    )
    if not link:
        return None
    href = str(link.get("href", "")) + " " + str(link.get("onclick", ""))
    match = REPORT_PATTERN.search(href)
    title = link.get_text(" ", strip=True)
    if not title or not title_allowed(title, config.filters):
        return None

    if match:
        category, report_id = match.group(2), match.group(1)
        detail_url = DETAIL_URL.format(category=category, report_id=report_id)
        item_key = report_id
    else:
        re_idx_match = re.search(r"reIdx=(\d+)", href)
        item_key = re_idx_match.group(1) if re_idx_match else str(hash(title))
        detail_url = str(link.get("href", str(config.list_url)))

    return DiscoveredItem(
        source_item_key=item_key,
        title=title,
        detail_url=HttpUrl(detail_url),
        published_at=_date(node.get_text(" ", strip=True)),
    )



def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group().replace(".", "-")) if match else None


def _published_at(soup: BeautifulSoup) -> date | None:
    return _date(soup.get_text(" ", strip=True))


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("div.tabPage.active")
    summary = node.get_text(" ", strip=True) if node else ""
    return re.sub(r"\s+", " ", summary).replace("요약 탭컨텐츠", "").strip() or None
