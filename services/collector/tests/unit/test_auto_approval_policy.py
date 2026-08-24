from datetime import UTC, date, datetime, timedelta

import pytest
from report_collector.domain.enums import DeliveryMode, RightsStatus
from report_collector.services.auto_approval_policy import (
    AutoApprovalCandidate,
    evaluate_candidate,
)

END = datetime(2026, 8, 21, 8, 35, tzinfo=UTC)
START = END - timedelta(hours=24)


def candidate(**changes: object) -> AutoApprovalCandidate:
    values: dict[str, object] = {
        "document_id": "document-1",
        "published_at": date(2026, 8, 21),
        "first_seen_at": END - timedelta(hours=1),
        "source_active": True,
        "source_healthy": True,
        "rights_status": RightsStatus.LINK_ONLY,
        "delivery_mode": DeliveryMode.DIRECT_OFFICIAL_FILE,
        "summary_status": "COMPLETED",
        "summary_kind": "ANALYZED",
        "why_it_matters": "실제 본문에서 확인한 정책적 의미입니다.",
        "key_tags": ("정책", "산업"),
        "confidence": 0.8,
        "source_url": "https://example.com/report/1",
        "duplicate_count": 0,
        "has_session_file_url": False,
    }
    values.update(changes)
    return AutoApprovalCandidate(**values)  # type: ignore[arg-type]


def test_complete_candidate_is_auto_approved() -> None:
    decision = evaluate_candidate(candidate(), START, END)
    assert decision.approved
    assert decision.reason_codes == ("ELIGIBLE",)


def test_press_release_uses_a_24_hour_window() -> None:
    seven_day_start = END - timedelta(days=7)
    old_press = candidate(
        source_content_type="PRESS_RELEASE",
        first_seen_at=END - timedelta(hours=25),
        published_at=(END - timedelta(hours=25)).date(),
    )
    decision = evaluate_candidate(old_press, seven_day_start, END)
    assert not decision.approved
    assert "OUTSIDE_COLLECTION_WINDOW" in decision.reason_codes


def test_analyzed_press_release_can_approve_when_source_is_degraded() -> None:
    press = candidate(source_content_type="PRESS_RELEASE", source_healthy=False)
    assert evaluate_candidate(press, START, END).approved


def test_report_keeps_the_full_seven_day_window() -> None:
    seven_day_start = END - timedelta(days=7)
    report = candidate(
        first_seen_at=END - timedelta(days=6),
        published_at=(END - timedelta(days=6)).date(),
    )
    assert evaluate_candidate(report, seven_day_start, END).approved


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"published_at": None}, "PUBLISHED_DATE_MISSING"),
        ({"source_healthy": False}, "SOURCE_UNHEALTHY"),
        ({"rights_status": RightsStatus.MANUAL_REVIEW}, "RIGHTS_REVIEW_REQUIRED"),
        ({"summary_kind": "UNAVAILABLE"}, "SUMMARY_UNAVAILABLE"),
        ({"confidence": 0.4}, "CONFIDENCE_LOW"),
        ({"duplicate_count": 1}, "DUPLICATE_CANDIDATE"),
        ({"has_session_file_url": True}, "SESSION_FILE_URL"),
    ],
)
def test_risky_candidate_is_held(changes: dict[str, object], reason: str) -> None:
    decision = evaluate_candidate(candidate(**changes), START, END)
    assert not decision.approved
    assert reason in decision.reason_codes
