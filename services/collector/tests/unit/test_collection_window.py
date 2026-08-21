from datetime import date

import pytest
from pydantic import HttpUrl
from report_collector.domain.enums import RightsStatus
from report_collector.domain.models import DiscoveredItem, SourceDocument
from report_collector.pipelines.collect_source import collect_source
from report_collector.repositories.source_repository import MemorySourceRepository


class DatedAdapter:
    async def discover(self, cursor: str | None):
        yield DiscoveredItem(
            source_item_key="old", title="지난 보고서", detail_url=HttpUrl("https://example.com/old"),
            published_at=date(2026, 8, 1),
        )
        yield DiscoveredItem(
            source_item_key="new", title="오늘 보고서", detail_url=HttpUrl("https://example.com/new"),
            published_at=date(2026, 8, 20),
        )

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        return SourceDocument(
            source_item_key=item.source_item_key, title=item.title, institution="가상 기관",
            detail_url=item.detail_url, published_at=item.published_at, rights_status=RightsStatus.LINK_ONLY,
        )


@pytest.mark.asyncio
async def test_collection_skips_items_older_than_window() -> None:
    repository = MemorySourceRepository()

    result = await collect_source(
        "fixture", DatedAdapter(), repository, oldest_published_at=date(2026, 8, 14), max_items=20
    )

    assert result.discovered == 1
    assert ("fixture", "new") in repository.documents
    assert ("fixture", "old") not in repository.documents


class DetailDateAdapter:
    def __init__(self, published_at: date | None) -> None:
        self.published_at = published_at

    async def discover(self, cursor: str | None):
        yield DiscoveredItem(
            source_item_key="unknown-date",
            title="날짜 미확인 보고서",
            detail_url=HttpUrl("https://example.com/unknown-date"),
            published_at=date(2026, 8, 21),
        )

    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        return SourceDocument(
            source_item_key=item.source_item_key,
            title=item.title,
            institution="가상 기관",
            detail_url=item.detail_url,
            published_at=self.published_at,
            rights_status=RightsStatus.LINK_ONLY,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("published_at", [None, date(2026, 8, 19), date(2026, 8, 22)])
async def test_collection_requires_a_verified_date_inside_the_window(
    published_at: date | None,
) -> None:
    repository = MemorySourceRepository()

    await collect_source(
        "fixture",
        DetailDateAdapter(published_at),
        repository,
        oldest_published_at=date(2026, 8, 20),
        latest_published_at=date(2026, 8, 21),
    )

    assert repository.documents == {}


class MissingListDateAdapter(DetailDateAdapter):
    async def discover(self, cursor: str | None):
        yield DiscoveredItem(
            source_item_key="detail-date",
            title="상세 날짜 확인 보고서",
            detail_url=HttpUrl("https://example.com/detail-date"),
            published_at=None,
        )


@pytest.mark.asyncio
async def test_collection_uses_detail_date_when_list_date_is_missing() -> None:
    repository = MemorySourceRepository()

    result = await collect_source(
        "fixture",
        MissingListDateAdapter(date(2026, 8, 21)),
        repository,
        oldest_published_at=date(2026, 8, 20),
        latest_published_at=date(2026, 8, 21),
    )

    assert result.discovered == 1
    assert ("fixture", "detail-date") in repository.documents
