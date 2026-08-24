from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from pydantic import HttpUrl
from report_collector.adapters.base import SourceAdapter
from report_collector.domain.enums import RightsStatus
from report_collector.domain.models import DiscoveredItem, SourceDocument, SourceHealthResult
from report_collector.pipelines.collect_source import collect_source
from report_collector.repositories.source_repository import MemorySourceRepository


class FailingDetailAdapter(SourceAdapter):
    def __init__(self, discover_count: int = 3, fail_detail: bool = True) -> None:
        self.discover_count = discover_count
        self.fail_detail = fail_detail

    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        for i in range(self.discover_count):
            yield DiscoveredItem(
                source_item_key=f"item-{i}",
                title=f"Report {i}",
                detail_url=HttpUrl(f"https://example.org/item-{i}"),
                published_at=date(2026, 8, 24),
            )

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        if self.fail_detail:
            raise RuntimeError("Detail page fetch failed")
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution="Example Inst",
            detail_url=item.detail_url,
            published_at=item.published_at,
            rights_status=RightsStatus.LINK_ONLY,
        )

    async def health_check(self) -> SourceHealthResult:
        return SourceHealthResult(healthy=True, checked_at=datetime.now(UTC), message="ok")


@pytest.mark.asyncio
async def test_failed_runs_never_produce_negative_new_counts() -> None:
    repository = MemorySourceRepository()
    adapter = FailingDetailAdapter(discover_count=3, fail_detail=True)

    result = await collect_source(
        source_id="kotra-test",
        adapter=adapter,
        repository=repository,
        oldest_published_at=date(2026, 8, 20),
        latest_published_at=date(2026, 8, 24),
    )

    assert result.discovered == 3
    assert result.failed == 3
    assert result.new_count == 0
    assert result.updated_count == 0

    last_run = repository.runs[-1]
    assert last_run["discovered"] == 3
    assert last_run["failed"] == 3
    assert last_run["new_count"] >= 0
    assert last_run["new_count"] == 0
    assert last_run["updated_count"] == 0


@pytest.mark.asyncio
async def test_success_runs_track_new_and_updated_counts() -> None:
    repository = MemorySourceRepository()
    adapter = FailingDetailAdapter(discover_count=2, fail_detail=False)

    # First run: 2 new items
    result1 = await collect_source(
        source_id="inst-test",
        adapter=adapter,
        repository=repository,
    )
    assert result1.discovered == 2
    assert result1.new_count == 2
    assert result1.updated_count == 0
    assert result1.failed == 0

    # Second run with same items: 2 updated/existing items
    result2 = await collect_source(
        source_id="inst-test",
        adapter=adapter,
        repository=repository,
    )
    assert result2.discovered == 2
    assert result2.new_count == 0
    assert result2.updated_count == 2
    assert result2.failed == 0
