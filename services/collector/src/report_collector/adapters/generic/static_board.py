from collections.abc import AsyncIterator
from datetime import UTC, datetime

from report_collector.adapters.base import SourceAdapter
from report_collector.domain.models import (
    DiscoveredItem,
    SourceConfig,
    SourceDocument,
    SourceHealthResult,
)
from report_collector.providers.http.http_client import PublicHttpClient

from .html_parser import parse_detail, parse_list


class StaticBoardAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, http: PublicHttpClient) -> None:
        self.config = config
        self.http = http

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        html = await self.http.fetch_text(str(self.config.list_url))
        for item in parse_list(html, self.config):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        html = await self.http.fetch_text(str(item.detail_url))
        return parse_detail(html, item, self.config)

    async def health_check(self) -> SourceHealthResult:
        try:
            html = await self.http.fetch_text(str(self.config.list_url))
            count = len(parse_list(html, self.config))
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
