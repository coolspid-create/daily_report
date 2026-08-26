import re
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

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


class IbksResearchAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, _: PublicHttpClient, browser: BrowserRenderer | None
    ) -> None:
        if browser is None:
            raise ValueError("IBKS research requires the public rendered page")
        self.config = config
        self.browser = browser
        self.download_urls: dict[str, HttpUrl] = {}

    async def _items(self) -> list[DiscoveredItem]:
        html = await self.browser.render(
            str(self.config.list_url), "li a.down", self.config.browser.timeout_ms
        )
        soup = BeautifulSoup(html, "html.parser")
        items: list[DiscoveredItem] = []
        for row in soup.select("li:has(a.down):has(p.tit)"):
            title_node = row.select_one("p.tit")
            date_node = row.select_one(".date")
            download = row.select_one("a.down[href]")
            if not title_node or not download:
                continue
            href = str(download.get("href", ""))
            match = re.search(r"[?&]seq=(\d+)", href)
            if not match:
                continue
            source_item_key = f"ibks-{match.group(1)}"
            self.download_urls[source_item_key] = HttpUrl(
                urljoin(str(self.config.list_url), href)
            )
            items.append(
                DiscoveredItem(
                    source_item_key=source_item_key,
                    title=title_node.get_text(" ", strip=True),
                    detail_url=HttpUrl(f"{self.config.list_url}?seq={match.group(1)}"),
                    published_at=_date(date_node.get_text(" ", strip=True) if date_node else ""),
                )
            )
        if not items:
            raise SourceParseError("IBKS rendered research items not found")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in await self._items():
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        attachment_url = self.download_urls[item.source_item_key]
        url = str(attachment_url)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=item.published_at,
            attachments=[
                Attachment(
                    url=attachment_url,
                    file_name=f"{PurePosixPath(urlparse(url).path).stem}-{item.source_item_key}.pdf",
                    declared_type="application/pdf",
                )
            ],
            official_summary=item.title,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(await self._items())
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{count} public IBKS reports parsed",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )


def _date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y.%m.%d").date()
    except ValueError:
        return None
