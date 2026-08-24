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
    collected_count: int = 0
    failed_sources: int = 0


def run_daily_publication(
    collect: Callable[[], object | None],
    auto_review: Callable[[], AutoReviewSummary],
    publish: Callable[[], SnapshotBuildResult],
    deliver: Callable[[SnapshotBuildResult], int],
    dry_run: bool,
) -> DailyPublicationOutcome:
    collect_res = collect()
    if isinstance(collect_res, tuple) and len(collect_res) >= 2:
        failed_sources, new_count = int(collect_res[0]), int(collect_res[1])
    elif hasattr(collect_res, "failed_sources") and hasattr(collect_res, "new_documents_count"):
        failed_sources = int(collect_res.failed_sources)
        new_count = int(collect_res.new_documents_count)
    elif isinstance(collect_res, (int, float)):
        failed_sources, new_count = int(collect_res), 0
    else:
        failed_sources, new_count = 0, 0

    review = auto_review()
    if dry_run:
        return DailyPublicationOutcome("DRY_RUN", review, None, 0, collected_count=new_count, failed_sources=failed_sources)
    publication = publish()
    if publication.document_count == 0:
        status = "PARTIAL" if failed_sources else "NO_CONTENT"
        return DailyPublicationOutcome(status, review, publication, 0, collected_count=new_count, failed_sources=failed_sources)
    try:
        telegram_count = deliver(publication)
    except Exception:
        return DailyPublicationOutcome("PARTIAL", review, publication, 0, collected_count=new_count, failed_sources=failed_sources)
    status = "PARTIAL" if failed_sources else "PUBLISHED"
    return DailyPublicationOutcome(status, review, publication, telegram_count, collected_count=new_count, failed_sources=failed_sources)
