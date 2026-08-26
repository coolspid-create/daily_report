from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import PurePosixPath
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

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


class OfficialTelegramResearchAdapter(SourceAdapter):
    def __init__(
        self, config: SourceConfig, http: PublicHttpClient, _: BrowserRenderer | None = None
    ) -> None:
        self.config = config
        self.http = http
        self.resolved: dict[str, str] = {}

    def _parse_messages(self, html: str) -> list[tuple[DiscoveredItem, str]]:
        soup = BeautifulSoup(html, "html.parser")
        parsed: list[tuple[DiscoveredItem, str]] = []
        for message in soup.select(".tgme_widget_message[data-post]"):
            text_node = message.select_one(".tgme_widget_message_text")
            time_node = message.select_one("time[datetime]")
            if not text_node or not time_node:
                continue
            links = [str(a.get("href")) for a in text_node.find_all("a", href=True)]
            report_url = self._select_report_link(links)
            if not report_url:
                continue
            raw_title = text_node.get_text(" ", strip=True)
            title = raw_title.split("▶", 1)[0].split("◆ 보고서", 1)[0].strip()[:300]
            post_key = str(message.get("data-post", "")).replace("/", "-")
            published_at = (
                datetime.fromisoformat(str(time_node["datetime"]).replace("Z", "+00:00"))
                .astimezone(ZoneInfo("Asia/Seoul"))
                .date()
            )
            parsed.append(
                (
                    DiscoveredItem(
                        source_item_key=post_key,
                        title=title,
                        detail_url=HttpUrl(report_url.replace("http://", "https://")),
                        published_at=published_at,
                    ),
                    raw_title[:3000],
                )
            )
        return parsed

    def _select_report_link(self, links: list[str]) -> str | None:
        if self.config.id == "kiwoom-research":
            return next((url for url in links if "bbn.kiwoom.com/" in url), None)
        return next((url for url in links if "buly.kr/" in url), None)

    async def _items(self, resolve: bool) -> list[DiscoveredItem]:
        messages = self._parse_messages(await self.http.fetch_text(str(self.config.list_url)))
        items: list[DiscoveredItem] = []
        for item, _ in messages:
            if resolve and self.config.id == "sk-securities-research":
                result = await self.http.fetch(str(item.detail_url), max_bytes=25_000_000)
                final_url = result.final_url.replace("http://", "https://")
                parsed = urlparse(final_url)
                if (
                    not parsed.hostname
                    or not parsed.hostname.endswith("sks.co.kr")
                    or "/data1/research/" not in parsed.path
                ):
                    continue
                self.resolved[item.source_item_key] = final_url
            items.append(item)
        if not items:
            raise SourceParseError(f"No official report links found for {self.config.id}")
        return items

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in await self._items(resolve=True):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        final_url = self.resolved.get(item.source_item_key, str(item.detail_url)).replace(
            "http://", "https://"
        )
        parsed = urlparse(final_url)
        name = PurePosixPath(parsed.path).name or f"{item.source_item_key}.pdf"
        if not name.lower().endswith(".pdf"):
            name = f"{name}.pdf"
        official_url = HttpUrl(final_url)
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=official_url,
            published_at=item.published_at,
            attachments=[
                Attachment(url=official_url, file_name=name, declared_type="application/pdf")
            ],
            official_summary=item.title,
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(await self._items(resolve=False))
            return SourceHealthResult(
                healthy=True,
                checked_at=datetime.now(UTC),
                message=f"{count} official channel report links parsed",
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
