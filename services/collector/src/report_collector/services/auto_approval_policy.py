from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from report_collector.domain.enums import DeliveryMode, RightsStatus

POLICY_MIN_CONFIDENCE = 0.65


@dataclass(frozen=True)
class AutoApprovalCandidate:
    document_id: str
    published_at: date | None
    first_seen_at: datetime
    source_active: bool
    source_healthy: bool
    rights_status: RightsStatus
    delivery_mode: DeliveryMode
    summary_status: str
    summary_kind: str | None
    why_it_matters: str | None
    key_tags: tuple[str, ...]
    confidence: float | None
    source_url: str
    duplicate_count: int
    has_session_file_url: bool
    source_content_type: str = "REPORT"


@dataclass(frozen=True)
class AutoApprovalDecision:
    document_id: str
    approved: bool
    reason_codes: tuple[str, ...]


def evaluate_candidate(
    candidate: AutoApprovalCandidate,
    window_start: datetime,
    window_end: datetime,
) -> AutoApprovalDecision:
    reasons: list[str] = []
    effective_start = window_start
    if candidate.source_content_type == "PRESS_RELEASE":
        effective_start = max(window_start, window_end - timedelta(hours=24))
    if not effective_start <= candidate.first_seen_at <= window_end:
        reasons.append("OUTSIDE_COLLECTION_WINDOW")
    if candidate.published_at is None:
        reasons.append("PUBLISHED_DATE_MISSING")
    elif not effective_start.date() <= candidate.published_at <= window_end.date():
        reasons.append("PUBLISHED_DATE_OUTSIDE_WINDOW")
    if not candidate.source_active:
        reasons.append("SOURCE_INACTIVE")
    elif candidate.source_content_type != "PRESS_RELEASE" and not candidate.source_healthy:
        reasons.append("SOURCE_UNHEALTHY")
    if candidate.rights_status not in {
        RightsStatus.LINK_ONLY,
        RightsStatus.FILE_UPLOAD_ALLOWED,
    }:
        reasons.append("RIGHTS_REVIEW_REQUIRED")
    if candidate.delivery_mode is DeliveryMode.BLOCKED:
        reasons.append("DELIVERY_BLOCKED")
    if candidate.summary_status != "COMPLETED":
        reasons.append("SUMMARY_INCOMPLETE")
    if candidate.summary_kind not in {"ANALYZED", "OFFICIAL_ABSTRACT"}:
        reasons.append("SUMMARY_UNAVAILABLE")
    if not candidate.why_it_matters or not candidate.why_it_matters.strip():
        reasons.append("SUMMARY_EMPTY")
    if not 1 <= len(candidate.key_tags) <= 3:
        reasons.append("KEY_TAGS_INVALID")
    if candidate.confidence is None or candidate.confidence < POLICY_MIN_CONFIDENCE:
        reasons.append("CONFIDENCE_LOW")
    if not _valid_official_url(candidate.source_url):
        reasons.append("SOURCE_URL_INVALID")
    if candidate.has_session_file_url:
        reasons.append("SESSION_FILE_URL")
    if candidate.duplicate_count > 0:
        reasons.append("DUPLICATE_CANDIDATE")
    return AutoApprovalDecision(candidate.document_id, not reasons, tuple(reasons or ["ELIGIBLE"]))


def _valid_official_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)
