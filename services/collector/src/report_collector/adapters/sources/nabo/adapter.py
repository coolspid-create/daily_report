import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

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

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class NaboAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredItem] = []
        for node in soup.select(".item_wrap"):
            link = node.select_one(".report_name a[href*='View.do']")
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            item_key = parse_qs(urlparse(str(link["href"])).query).get("idx", [""])[0]
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
            raise SourceParseError("NABO report list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in self._parse_list(await self.http.fetch_text(str(self.config.list_url))):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        soup = BeautifulSoup(await self.http.fetch_text(str(item.detail_url)), "html.parser")
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=_date(soup.get_text(" ", strip=True)) or item.published_at,
            attachments=_attachments(soup, str(item.detail_url)),
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


def _date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    return date.fromisoformat(match.group()) if match else None


def _attachments(soup: BeautifulSoup, base_url: str) -> list[Attachment]:
    results: list[Attachment] = []
    for link in soup.select("a[href*='/board/file/down.do?']"):
        name = link.get_text(" ", strip=True) or "nabo-report.pdf"
        extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        declared = "application/pdf" if extension == "pdf" else None
        results.append(
            Attachment(
                url=HttpUrl(urljoin(base_url, str(link["href"]))),
                file_name=name,
                declared_type=declared,
            )
        )
    return results


def _summary(soup: BeautifulSoup) -> str | None:
    node = soup.select_one(".content, .view_content, .board_view")
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip() if node else ""
    return text[:3000] or None
