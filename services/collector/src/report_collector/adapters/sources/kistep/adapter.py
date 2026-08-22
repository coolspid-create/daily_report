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

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class KistepAdapter(SourceAdapter):
    """KISTEP 연구보고서와 브리프의 공개 HTML을 수집한다."""

    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        selector = self.config.selectors.list_item if self.config.selectors else ""
        results: list[DiscoveredItem] = []
        for node in soup.select(selector):
            link = node.select_one("strong.title a[href]")
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            item_key = _item_key(str(link.get("href", "")))
            if not item_key or not title_allowed(title, self.config.filters):
                continue
            results.append(
                DiscoveredItem(
                    source_item_key=item_key,
                    title=title,
                    detail_url=HttpUrl(urljoin(str(self.config.list_url), str(link["href"]))),
                    published_at=_date(node.get_text(" ", strip=True)),
                )
            )
        if not results:
            raise SourceParseError("KISTEP publication list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        soup = BeautifulSoup(html, "html.parser")
        attachments = _attachments(soup, str(item.detail_url), item.source_item_key)
        if not attachments:
            listing = BeautifulSoup(
                await self.http.fetch_text(str(self.config.list_url)), "html.parser"
            )
            attachments = _attachments(listing, str(self.config.list_url), item.source_item_key)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=attachments,
            official_summary=_summary(soup),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(self._parse_list(await self.http.fetch_text(str(self.config.list_url))))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _item_key(href: str) -> str | None:
    query = parse_qs(urlparse(href).query)
    values = query.get("rpt_no") or query.get("list_no")
    return values[0] if values else None


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group()) if match else None


def _attachments(soup: BeautifulSoup, base_url: str, item_key: str) -> list[Attachment]:
    links = [
        link
        for link in soup.select("a[href*='Download'], a[href*='download']")
        if item_key in str(link.get("href", ""))
    ]
    return [
        Attachment(
            url=HttpUrl(urljoin(base_url, str(link["href"]))),
            file_name=f"kistep-{item_key}.pdf",
            declared_type="application/pdf",
        )
        for link in links[:1]
    ]


def _summary(soup: BeautifulSoup) -> str | None:
    content = soup.select_one(".board_view .view_con, .board_view .board_txt, .board_view")
    if not isinstance(content, Tag):
        return None
    text = re.sub(r"\s+", " ", content.get_text(" ", strip=True)).strip()
    return text[:3000] or None
