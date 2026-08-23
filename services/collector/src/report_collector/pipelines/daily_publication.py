from collections.abc import Callable
from dataclasses import dataclass

from report_collector.cli.snapshot_command import SnapshotBuildResult
from report_collector.pipelines.auto_review_documents import AutoReviewSummary


@dataclass(frozen=True)
class DailyPublicationOutcome:
    status: str
    review: AutoReviewSummary
    publication: SnapshotBuildResult | None
    telegram_count: int


def run_daily_publication(
    collect: Callable[[], int | None],
    auto_review: Callable[[], AutoReviewSummary],
    publish: Callable[[], SnapshotBuildResult],
    deliver: Callable[[SnapshotBuildResult], int],
    dry_run: bool,
) -> DailyPublicationOutcome:
    failed_sources = collect() or 0
    review = auto_review()
    if dry_run:
        return DailyPublicationOutcome("DRY_RUN", review, None, 0)
    publication = publish()
    if publication.document_count == 0:
        status = "PARTIAL" if failed_sources else "NO_CONTENT"
        return DailyPublicationOutcome(status, review, publication, 0)
    try:
        telegram_count = deliver(publication)
    except Exception:
        return DailyPublicationOutcome("PARTIAL", review, publication, 0)
    status = "PARTIAL" if failed_sources else "PUBLISHED"
    return DailyPublicationOutcome(status, review, publication, telegram_count)
