from report_collector.cli.daily_publish_command import _should_send_no_content_notice
from report_collector.cli.snapshot_command import SnapshotBuildResult
from report_collector.pipelines.auto_review_documents import AutoReviewSummary
from report_collector.pipelines.daily_publication import DailyPublicationOutcome


def test_telegram_notice_only_sent_when_all_zero() -> None:
    empty_pub = SnapshotBuildResult("pub", "snap", 0, {})
    has_pub = SnapshotBuildResult("pub", "snap", 3, {})

    # Case 1: All zero and scheduled -> Send notice
    outcome_all_zero = DailyPublicationOutcome(
        status="NO_CONTENT",
        review=AutoReviewSummary(candidate_count=0, approved_count=0, exception_count=0),
        publication=empty_pub,
        telegram_count=0,
        collected_count=0,
    )
    assert _should_send_no_content_notice(outcome_all_zero, scheduled_run=True) is True
    assert _should_send_no_content_notice(outcome_all_zero, scheduled_run=False) is False

    # Case 2: New items were collected but not published (e.g. held for review) -> DO NOT send "no content"
    outcome_with_new_collected = DailyPublicationOutcome(
        status="NO_CONTENT",
        review=AutoReviewSummary(candidate_count=2, approved_count=0, exception_count=2),
        publication=empty_pub,
        telegram_count=0,
        collected_count=2,
    )
    assert _should_send_no_content_notice(outcome_with_new_collected, scheduled_run=True) is False

    # Case 3: Exception candidates waiting for review -> DO NOT send "no content"
    outcome_with_exceptions = DailyPublicationOutcome(
        status="NO_CONTENT",
        review=AutoReviewSummary(candidate_count=1, approved_count=0, exception_count=1),
        publication=empty_pub,
        telegram_count=0,
        collected_count=0,
    )
    assert _should_send_no_content_notice(outcome_with_exceptions, scheduled_run=True) is False

    # Case 4: Reports published -> DO NOT send "no content"
    outcome_published = DailyPublicationOutcome(
        status="PUBLISHED",
        review=AutoReviewSummary(candidate_count=3, approved_count=3, exception_count=0),
        publication=has_pub,
        telegram_count=1,
        collected_count=3,
    )
    assert _should_send_no_content_notice(outcome_published, scheduled_run=True) is False
