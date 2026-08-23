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

_DETAIL = re.compile(r"fn_edit\(['\"]detail['\"],\s*['\"](\d+)")
_DATE = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")


class NafiResearchAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [
            item
            for node in soup.select("tbody tr, .board_list li, .photo_listW li")
            if (item := _item(node, self.config))
        ]
        if not items:
            raise SourceParseError("NAFI research list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        content = next(
            (
                soup.select_one(selector)
                for selector in (".contents", ".board_view", ".view_cont", "article")
                if soup.select_one(selector)
            ),
            None,
        )
        text = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip() if content else ""
        return SourceDocument(source_item_key=item.source_item_key, title=item.title, institution=self.config.name, detail_url=item.detail_url,
            published_at=item.published_at, official_summary=text[:3000] or None, rights_status=self.config.rights_default)

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[onclick*='fn_edit']")
    match = _DETAIL.search(str(link.get("onclick", ""))) if link else None
    title = link.get_text(" ", strip=True) if link else ""
    if not match or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(source_item_key=match.group(1), title=title,
        detail_url=HttpUrl(f"https://nafi.re.kr/home/kor/board.do?menuPos=13&act=detail&idx={match.group(1)}"), published_at=_date(node.get_text(" ", strip=True)))


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None
