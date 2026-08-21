from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date

from report_collector.adapters.base import SourceAdapter
from report_collector.domain.models import SourceDocument
from report_collector.repositories.source_repository import SourceRepository


@dataclass(frozen=True)
class CollectionResult:
    source_id: str
    discovered: int
    failed: int
    cursor_after: str | None


async def collect_source(
    source_id: str,
    adapter: SourceAdapter,
    repository: SourceRepository,
    after_save: Callable[[str, SourceDocument], Awaitable[None]] | None = None,
    oldest_published_at: date | None = None,
    latest_published_at: date | None = None,
    max_items: int | None = None,
    resume_from_cursor: bool = True,
) -> CollectionResult:
    cursor = repository.get_cursor(source_id) if resume_from_cursor else None
    discovered = 0
    failed = 0
    newest_key: str | None = None
    async for item in adapter.discover(cursor):
        if item.published_at is not None and not _within_publication_window(
            item.published_at, oldest_published_at, latest_published_at
        ):
            continue
        if max_items is not None and discovered >= max_items:
            break
        try:
            document = await adapter.fetch_detail(item)
            if not _within_publication_window(
                document.published_at, oldest_published_at, latest_published_at
            ):
                continue
            newest_key = newest_key or item.source_item_key
            discovered += 1
            document_id = repository.save_document(source_id, document)
            if document_id and after_save:
                await after_save(document_id, document)
        except Exception:
            failed += 1
    repository.finish_run(source_id, newest_key or cursor, discovered, failed)
    return CollectionResult(source_id, discovered, failed, newest_key or cursor)


def _within_publication_window(
    published_at: date | None, oldest: date | None, latest: date | None
) -> bool:
    if oldest is None and latest is None:
        return True
    if published_at is None:
        return False
    return (oldest is None or published_at >= oldest) and (latest is None or published_at <= latest)
