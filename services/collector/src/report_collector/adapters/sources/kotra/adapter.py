import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

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

DATE_PATTERN = re.compile(r"\d{4}[.-]\d{2}[.-]\d{2}")


class KotraMarketNewsAdapter(SourceAdapter):
    """공개 목록ㆍ상세 HTML과 공식 파일 링크만 읽는 KOTRA 수집기."""

    def __init__(self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = [item for node in soup.select(".mNewsList .list") if (item := _item(node, self.config))]
        if not items:
            raise SourceParseError("KOTRA market news list structure changed")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key, title=item.title, institution=self.config.name,
            detail_url=item.detail_url, published_at=_date(_detail_date_text(soup)),
            attachments=_attachments(html, str(item.detail_url)), official_summary=_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))
            return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed")
        except Exception as error:
            return SourceHealthResult(healthy=False, checked_at=datetime.now(UTC), message=str(error))


def _item(node: Tag, config: SourceConfig) -> DiscoveredItem | None:
    link = node.select_one("a[href*='actionKotraBoardDetail.do']")
    title_node = node.select_one("strong.tit")
    href = str(link.get("href", "")) if link else ""
    key = parse_qs(urlparse(href).query).get("pNttSn", [None])[0]
    title = title_node.get_text(" ", strip=True) if title_node else ""
    if not key or not title or not title_allowed(title, config.filters):
        return None
    return DiscoveredItem(source_item_key=key, title=title, detail_url=HttpUrl(urljoin(str(config.list_url), href)))


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group().replace(".", "-")) if match else None


def _detail_date_text(soup: BeautifulSoup) -> str:
    date_node = soup.select_one(".date")
    return date_node.get_text(" ", strip=True) if date_node else soup.get_text(" ", strip=True)


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("meta[name='description']") or soup.select_one(".view_txt")
    text = node.get("content", "") if node and node.name == "meta" else node.get_text(" ", strip=True) if node else ""
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    return normalized[:3000].rsplit(" ", 1)[0] if len(normalized) > 3000 else normalized or None


def _attachments(html: str, base_url: str) -> list[Attachment]:
    pattern = re.compile(r"(?:href|location\.href)\s*=\s*['\"]([^'\"]*(?:fileDown|download)[^'\"]*)", re.I)
    return [Attachment(url=HttpUrl(urljoin(base_url, match.group(1))), file_name="KOTRA_해외시장뉴스.pdf", declared_type="application/pdf") for match in pattern.finditer(html)]
