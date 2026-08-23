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

_ONCLICK = re.compile(r"goDetailPage\(['\"](\d+)['\"],\s*['\"]([A-Z_]+)['\"]\)")
_ROUTES = {"TRADE_FOCUS": "tradeFocus/tradeFocusDetail.do", "TRADE_BRIEF": "tradeBrief/tradeBriefDetail.do", "TRADE_REPORT": "commerceReport/commerceReportDetail.do", "ISSUE_BRIEF": "issueBrief/issueBriefDetail.do"}
_DATE = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")


class KitaReportAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        items: list[DiscoveredItem] = []
        for node in BeautifulSoup(html, "html.parser").select("ul.board-list-gallery li"):
            if (item := _item(node, self.config)) is not None:
                items.append(item)
        if not items:
            raise SourceParseError("KITA report list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        return SourceDocument(source_item_key=item.source_item_key, title=item.title, institution=self.config.name,
            detail_url=item.detail_url, published_at=item.published_at, attachments=_attachments(soup, str(item.detail_url)),
            official_summary=_summary(soup), rights_status=self.config.rights_default)

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one(".subject a")
    match = _ONCLICK.search(str(link.get("onclick", ""))) if link else None
    title = link.get_text(" ", strip=True) if link else ""
    route = _ROUTES.get(match.group(2)) if match else None
    if not match or not route or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(source_item_key=match.group(1), title=title,
        detail_url=HttpUrl(f"https://www.kita.net/researchTrade/report/{route}?no={match.group(1)}"), published_at=_date(node.get_text(" ", strip=True)))


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None


def _summary(soup: BeautifulSoup) -> str | None:
    node = next(
        (
            soup.select_one(selector)
            for selector in (".detail-body", ".view_cont", ".board_view", "article")
            if soup.select_one(selector)
        ),
        None,
    )
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text[:3000] or None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    return [Attachment(url=HttpUrl(urljoin(base_url, str(link["href"]))), file_name=link.get_text(" ", strip=True) or "KITA-report.pdf", declared_type="application/pdf")
            for link in soup.select("a[href]") if ".pdf" in str(link["href"]).lower() or "download" in str(link["href"]).lower()]
