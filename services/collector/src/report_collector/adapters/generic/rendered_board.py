from collections.abc import AsyncIterator

from report_collector.adapters.base import SourceAdapter
from report_collector.domain.models import (
    DiscoveredItem,
    SourceConfig,
    SourceDocument,
    SourceHealthResult,
)
from report_collector.providers.browser.base import BrowserRenderer

from .html_parser import parse_detail, parse_list


class RenderedBoardAdapter(SourceAdapter):
    def __init__(self, config: SourceConfig, browser: BrowserRenderer) -> None:
        self.config = config
        self.browser = browser

    async def _render(self, url: str, wait_for: str | None = None) -> str:
        return await self.browser.render(
            url, wait_for, self.config.browser.timeout_ms
        )

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for item in parse_list(
            await self._render(str(self.config.list_url), self.config.browser.wait_for), self.config
        ):
            if item.source_item_key == cursor:
                break
            yield item

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        return parse_detail(await self._render(str(item.detail_url)), item, self.config)

    async def health_check(self) -> SourceHealthResult:
        from datetime import UTC, datetime

        try:
            count = len(
                parse_list(
                    await self._render(str(self.config.list_url), self.config.browser.wait_for),
                    self.config,
                )
            )
            return SourceHealthResult(
                healthy=True, checked_at=datetime.now(UTC), message=f"{count} items parsed"
            )
        except Exception as error:
            return SourceHealthResult(
                healthy=False, checked_at=datetime.now(UTC), message=str(error)
            )
