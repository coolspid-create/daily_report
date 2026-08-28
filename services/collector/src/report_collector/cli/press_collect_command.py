import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from report_collector.cli.collect_command import (
    CollectBatchSummary,
    collect_and_summarize,
    collect_sources_and_summarize,
)
from report_collector.cli.publish_approved_command import publish_approved_command
from report_collector.pipelines.auto_review_documents import auto_review_documents
from report_collector.repositories.supabase.postgres_source_repository import (
    load_retryable_press_source_slugs,
)


def press_collect_command(root: Path, timezone: str, window_hours: int, output_dir: Path) -> None:
    database_url = _required("DATABASE_URL")
    summary = _collect(root, database_url)
    now = datetime.now(ZoneInfo(timezone))
    review = auto_review_documents(
        database_url,
        now - timedelta(hours=window_hours),
        now,
        os.getenv("AUTO_APPROVAL_POLICY_VERSION", "2026-08-pilot-v2"),
        _enabled("AUTO_APPROVAL_ENABLED"),
        source_content_type="PRESS_RELEASE",
    )
    publication = publish_approved_command(root, timezone, output_dir, deliver=False)
    published = publication.document_count if publication else 0
    print(
        "press collection finished: "
        f"discovered={summary.discovered_count} new={summary.new_documents_count} "
        f"failed={summary.failed_sources} approved={review.approved_count} published={published} telegram=0"
    )


def _collect(root: Path, database_url: str) -> CollectBatchSummary:
    initial = collect_and_summarize(
        None,
        True,
        root / "config/sources",
        root / "contracts/source-config.schema.json",
        refresh_recent=True,
        content_type="PRESS_RELEASE",
    )
    retryable_sources = sorted(
        load_retryable_press_source_slugs(database_url, initial.failed_source_ids)
    )
    if not retryable_sources:
        return initial

    delay_seconds = int(os.getenv("PRESS_RETRY_DELAY_SECONDS", "60"))
    if delay_seconds > 0:
        print(
            f"retrying failed press sources after {delay_seconds}s: "
            f"{', '.join(retryable_sources)}"
        )
        time.sleep(delay_seconds)
    retry = collect_sources_and_summarize(
        retryable_sources,
        root / "config/sources",
        root / "contracts/source-config.schema.json",
        refresh_recent=True,
    )
    return _merge_collection_summaries(initial, retry, retryable_sources)


def _merge_collection_summaries(
    initial: CollectBatchSummary,
    retry: CollectBatchSummary,
    retried_sources: list[str],
) -> CollectBatchSummary:
    unresolved = (set(initial.failed_source_ids) - set(retried_sources)) | set(retry.failed_source_ids)
    return CollectBatchSummary(
        failed_sources=len(unresolved),
        new_documents_count=initial.new_documents_count + retry.new_documents_count,
        discovered_count=initial.discovered_count + retry.discovered_count,
        failed_source_ids=tuple(sorted(unresolved)),
    )


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() in {"1", "true", "yes", "on"}


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
