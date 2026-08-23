from dataclasses import dataclass
from datetime import datetime

from report_collector.repositories.supabase.postgres_auto_review import (
    apply_auto_review_decisions,
    load_auto_review_candidates,
)
from report_collector.services.auto_approval_policy import evaluate_candidate


@dataclass(frozen=True)
class AutoReviewSummary:
    candidate_count: int
    approved_count: int
    exception_count: int


def auto_review_documents(
    database_url: str,
    window_start: datetime,
    window_end: datetime,
    policy_version: str,
    apply_changes: bool,
    source_slug: str | None = None,
) -> AutoReviewSummary:
    candidates = load_auto_review_candidates(database_url, window_start, window_end, source_slug)
    decisions = [evaluate_candidate(item, window_start, window_end) for item in candidates]
    if not apply_changes:
        approved = sum(decision.approved for decision in decisions)
        return AutoReviewSummary(len(candidates), approved, len(candidates) - approved)
    approved, held = apply_auto_review_decisions(database_url, decisions, policy_version)
    return AutoReviewSummary(len(candidates), approved, held)
