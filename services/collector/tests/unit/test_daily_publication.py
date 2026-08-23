from report_collector.cli.snapshot_command import SnapshotBuildResult
from report_collector.pipelines.auto_review_documents import AutoReviewSummary
from report_collector.pipelines.daily_publication import run_daily_publication


def _publication(count: int = 3) -> SnapshotBuildResult:
    return SnapshotBuildResult("publication", "snapshot", count, {})


def test_daily_publication_runs_in_order() -> None:
    events: list[str] = []
    outcome = run_daily_publication(
        lambda: events.append("collect"),
        lambda: (events.append("review") or AutoReviewSummary(4, 3, 1)),
        lambda: (events.append("publish") or _publication()),
        lambda _: (events.append("deliver") or 2),
        False,
    )
    assert events == ["collect", "review", "publish", "deliver"]
    assert outcome.status == "PUBLISHED"


def test_telegram_failure_does_not_rollback_publication() -> None:
    def fail(_: SnapshotBuildResult) -> int:
        raise RuntimeError("telegram unavailable")

    outcome = run_daily_publication(
        lambda: None,
        lambda: AutoReviewSummary(1, 1, 0),
        _publication,
        fail,
        False,
    )
    assert outcome.status == "PARTIAL"
    assert outcome.publication is not None


def test_dry_run_does_not_publish() -> None:
    outcome = run_daily_publication(
        lambda: None,
        lambda: AutoReviewSummary(2, 1, 1),
        lambda: (_ for _ in ()).throw(AssertionError()),
        lambda _: 0,
        True,
    )
    assert outcome.status == "DRY_RUN"


def test_no_content_with_source_failures_is_partial() -> None:
    outcome = run_daily_publication(
        lambda: 2,
        lambda: AutoReviewSummary(0, 0, 0),
        lambda: _publication(0),
        lambda _: 0,
        False,
    )

    assert outcome.status == "PARTIAL"
