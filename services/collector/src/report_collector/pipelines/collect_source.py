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
    new_count: int = 0
    updated_count: int = 0


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
    saved_new = 0
    saved_updated = 0
    failed = 0
    newest_key: str | None = None
    try:
        async for item in adapter.discover(cursor):
            if item.published_at is not None and not _within_publication_window(
                item.published_at, oldest_published_at, latest_published_at
            ):
                continue
            discovered += 1
            if max_items is not None and discovered > max_items:
                break
            try:
                document = await adapter.fetch_detail(item)
                if not _within_publication_window(
                    document.published_at, oldest_published_at, latest_published_at
                ):
                    continue
                newest_key = newest_key or item.source_item_key
                save_result = repository.save_document(source_id, document)
                document_id: str | None = None
                is_new: bool = False
                if isinstance(save_result, tuple):
                    document_id, is_new = save_result[0], bool(save_result[1])
                elif save_result:
                    document_id, is_new = str(save_result), True
                if is_new:
                    saved_new += 1
                else:
                    saved_updated += 1
                if document_id and after_save:
                    await after_save(document_id, document)
            except Exception:
                failed += 1
    finally:
        closer = getattr(adapter, "close", None)
        if callable(closer):
            await closer()
    repository.finish_run(
        source_id,
        newest_key or cursor,
        discovered=discovered,
        failed=failed,
        new_count=saved_new,
        updated_count=saved_updated,
    )
    return CollectionResult(
        source_id,
        discovered,
        failed,
        newest_key or cursor,
        new_count=saved_new,
        updated_count=saved_updated,
    )


def _within_publication_window(
    published_at: date | None, oldest: date | None, latest: date | None
) -> bool:
    if oldest is None and latest is None:
        return True
    if published_at is None:
        return False
    return (oldest is None or published_at >= oldest) and (latest is None or published_at <= latest)
