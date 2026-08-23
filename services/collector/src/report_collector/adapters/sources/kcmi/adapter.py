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

_VIEW = re.compile(r"viewpage\((\d+),")
_DATE = re.compile(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})")


class KcmiReportAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config, self.http = config, http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        items = [item for node in BeautifulSoup(html, "html.parser").select(".list") if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError("KCMI report list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        return SourceDocument(source_item_key=item.source_item_key, title=item.title, institution=self.config.name, detail_url=item.detail_url,
            published_at=item.published_at, attachments=_attachments(soup, str(item.detail_url)), official_summary=_summary(soup), rights_status=self.config.rights_default)

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[onclick*='viewpage']")
    title_node = node.select_one(".rpt_title strong")
    match = _VIEW.search(str(link.get("onclick", ""))) if link else None
    title = title_node.get_text(" ", strip=True) if title_node else ""
    if not match or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(source_item_key=match.group(1), title=title, detail_url=HttpUrl(f"https://www.kcmi.re.kr/report/report_view?report_no={match.group(1)}"), published_at=_date(node.get_text(" ", strip=True)))


def _date(text: str) -> date | None:
    match = _DATE.search(text)
    return date(*map(int, match.groups())) if match else None


def _summary(soup: BeautifulSoup) -> str | None:
    node = next((soup.select_one(selector) for selector in (".rpt_view", ".view_cont", "article") if soup.select_one(selector)), None)
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text[:3000] or None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    return [Attachment(url=HttpUrl(urljoin(base_url, str(link["href"]))), file_name="KCMI-report.pdf", declared_type="application/pdf")
            for link in soup.select("a[href*='downloadw'], a[href*='flexer/view']")]
