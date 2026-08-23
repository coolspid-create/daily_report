import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
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

_PATH = re.compile(r"/(?:annual|finance|economy)/(?:reportView|financeView|economyView)\?rpt_no=(\d+)")
_DATE = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")


class KcifPublicReportAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        found: dict[str, DiscoveredItem] = {}
        for link in soup.select("a[href]"):
            href = str(link["href"])
            match = _PATH.search(href)
            title = link.get_text(" ", strip=True)
            if not match or not title_allowed(title, self.config.filters):
                continue
            node = link.find_parent(["li", "tr", "div"]) or link
            found.setdefault(match.group(1), DiscoveredItem(source_item_key=match.group(1), title=title,
                detail_url=HttpUrl(urljoin(str(self.config.homepage_url), href)), published_at=_date(node.get_text(" ", strip=True))))
        if not found:
            raise SourceParseError("KCIF public report links not found")
        return list(found.values())

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        content = next((soup.select_one(selector) for selector in (".board_view", ".view_cont", "article") if soup.select_one(selector)), None)
        text = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip() if content else ""
        return SourceDocument(source_item_key=item.source_item_key, title=item.title, institution=self.config.name, detail_url=item.detail_url,
            published_at=item.published_at, attachments=_attachments(soup, str(item.detail_url)), official_summary=text[:3000] or None, rights_status=self.config.rights_default)

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    return [Attachment(url=HttpUrl(urljoin(base_url, str(link["href"]))), file_name=link.get_text(" ", strip=True) or "KCIF-report.pdf", declared_type="application/pdf")
            for link in soup.select("a[href]") if ".pdf" in str(link["href"]).lower()]
