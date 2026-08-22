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

DATE_PATTERN = re.compile(
    r"(?P<year>\d{4})\s*(?:[./-]|년)\s*(?P<month>\d{1,2})\s*(?:[./-]|월)\s*(?P<day>\d{1,2})(?:일)?"
)
DETAIL_PATTERN = re.compile(r"hmpeSeqNo=(\d+)")
DOWNLOAD_PATTERN = re.compile(r"downloadItem\(\d+,\s*(\d+)\)")


class HanaResearchAdapter(SourceAdapter):
    """공개 하나금융연구소 게시판과 공식 첨부파일만 연결합니다."""

    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select("li") if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError("Hana research list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key, title=item.title, institution=self.config.name,
            detail_url=item.detail_url, published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=_attachments(str(soup)), official_summary=_summary(soup), rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[onclick*='boardDetail'], a[href*='boardDetail'], a[href*='goPage']")
    reference = f"{link.get('href', '')} {link.get('onclick', '')}" if link else ""
    match = DETAIL_PATTERN.search(reference)
    title_node = node.select_one("p.tit")
    title = title_node.get_text(" ", strip=True) if title_node else link.get_text(" ", strip=True) if link else ""
    if not match or not title or not title_allowed(title, config.filters):
        return None
    href = f"/boardDetail.do?hmpeSeqNo={match.group(1)}"
    return DiscoveredItem(source_item_key=match.group(1), title=title, detail_url=HttpUrl(urljoin(str(config.list_url), href)), published_at=_date(node.get_text(" ", strip=True)))


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    if not match:
        return None
    try:
        return date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    except ValueError:
        return None


def _attachments(html: str) -> list[Attachment]:
    return [Attachment(url=HttpUrl(f"https://www.hanaif.re.kr/dev/hanaifFileDownload.jsp?seq={match.group(1)}"), file_name="하나금융연구소_공식자료.pdf", declared_type="application/pdf") for match in DOWNLOAD_PATTERN.finditer(html)]


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one(".boardView, .viewCont, .contents")
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text or None
