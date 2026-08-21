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

PUB_PATTERN = re.compile(r"pub_no=(\d+)")
DOWNLOAD_PATTERN = re.compile(r"location\.href=['\"]([^'\"]*?/file/download\?[^'\"]+)['\"]")
DATE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}")


class KdiRenderedAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None
    ) -> None:
        if browser is None:
            raise ValueError("KDI rendered adapter requires a browser")
        self.config = config
        self.browser = browser

    async def _render(self, url: str, wait_for: str | None) -> str:
        return await self.browser.render(url, wait_for, self.config.browser.timeout_ms)

    def _parse_list(self, html: str) -> list[DiscoveredItem]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredItem] = []
        for node in soup.select("div.page_list-group > ul > li"):
            link = node.select_one("a[href*='reportView?pub_no=']")
            title = node.select_one("div.rpt_tit strong")
            match = PUB_PATTERN.search(str(link.get("href", ""))) if link else None
            if not link or not title or not match:
                continue
            title_text = title.get_text(" ", strip=True)
            if not title_allowed(title_text, self.config.filters):
                continue
            url = urljoin(str(self.config.list_url), str(link["href"]))
            results.append(
                DiscoveredItem(
                    source_item_key=match.group(1),
                    title=title_text,
                    detail_url=HttpUrl(url),
                )
            )
        if not results:
            raise SourceParseError("KDI report list structure changed")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self._render(str(self.config.list_url), self.config.browser.wait_for)
        for item in self._parse_list(html):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self._render(str(item.detail_url), "div.view_fixed-info")
        match = DOWNLOAD_PATTERN.search(html)
        info = BeautifulSoup(html, "html.parser").select_one("div.view_fixed-info")
        date_match = DATE_PATTERN.search(info.get_text(" ", strip=True)) if info else None
        attachments = []
        if match:
            url = urljoin(str(item.detail_url), match.group(1))
            attachments.append(
                Attachment(
                    url=HttpUrl(url),
                    file_name=f"kdi-{item.source_item_key}.pdf",
                    declared_type="application/pdf",
                )
            )
        published = (
            date.fromisoformat(date_match.group().replace(".", "-"))
            if date_match
            else item.published_at
        )
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=published,
            attachments=attachments,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self._render(str(self.config.list_url), self.config.browser.wait_for)
            count = len(self._parse_list(html))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
