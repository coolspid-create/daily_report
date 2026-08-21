from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from html import unescape
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
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.services.source_filter_service import title_allowed


def _published(value: str) -> date | None:
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


class RssAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient) -> None:
        self.config = config
        self.http = http
        self.attachments: dict[str, list[Attachment]] = {}
        self.official_summaries: dict[str, str] = {}

    async def _items(self) -> list[DiscoveredItem]:
        xml = await self.http.fetch_text(str(self.config.list_url))
        soup = BeautifulSoup(xml, "xml")
        results: list[DiscoveredItem] = []
        for node in soup.find_all(["item", "entry"]):
            title = node.find("title")
            link = node.find("link")
            link_href = link.get("href") if link else None
            href = str(link_href) if link_href else link.get_text(strip=True) if link else ""
            guid = node.find("guid") or node.find("id")
            key: str = guid.get_text(strip=True) if guid else href
            published = node.find("pubDate") or node.find("published") or node.find("updated")
            if not title or not href or not key:
                continue
            title_text = title.get_text(" ", strip=True)
            if not title_allowed(title_text, self.config.filters):
                continue
            item = DiscoveredItem(
                source_item_key=key,
                title=title_text,
                detail_url=HttpUrl(urljoin(str(self.config.list_url), href)),
                published_at=_published(published.get_text(strip=True)) if published else None,
            )
            results.append(item)
            summary = node.find("description") or node.find("summary") or node.find("content")
            if summary:
                text = BeautifulSoup(
                    unescape(summary.get_text(" ", strip=True)), "html.parser"
                ).get_text(" ", strip=True)
                if text:
                    self.official_summaries[key] = text[:3_000]
            enclosure = node.find("enclosure")
            if enclosure and enclosure.get("url"):
                url = urljoin(str(self.config.list_url), str(enclosure["url"]))
                extension = url.split("?", 1)[0].rsplit(".", 1)[-1].lower()
                if extension not in self.config.filters.allowed_extensions:
                    continue
                enclosure_type = enclosure.get("type")
                self.attachments[key] = [
                    Attachment(
                        url=HttpUrl(url),
                        file_name=url.rsplit("/", 1)[-1] or "report.pdf",
                        declared_type=str(enclosure_type) if enclosure_type else None,
                    )
                ]
        if not results:
            raise SourceParseError("RSS/Atom feed did not contain report entries")
        return results

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in await self._items():
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        if item.source_item_key not in self.attachments:
            await self._items()
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution=self.config.name,
            detail_url=item.detail_url,
            published_at=item.published_at,
            attachments=self.attachments.get(item.source_item_key, []),
            official_summary=self.official_summaries.get(item.source_item_key),
            rights_status=self.config.rights_default,
        )

    async def health_check(self) -> SourceHealthResult:
        try:
            count = len(await self._items())
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} entries parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
