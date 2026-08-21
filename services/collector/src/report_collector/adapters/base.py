from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from report_collector.domain.models import DiscoveredItem, SourceDocument, SourceHealthResult


class SourceAdapter(ABC):
    @abstractmethod
    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        if False:
            yield DiscoveredItem(source_item_key="", title="", detail_url="https://example.com")

    @abstractmethod
    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument: ...

    @abstractmethod
    async def health_check(self) -> SourceHealthResult: ...
