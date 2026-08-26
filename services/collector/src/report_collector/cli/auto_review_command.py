import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from report_collector.pipelines.auto_review_documents import auto_review_documents


def auto_review_command(
    timezone: str,
    window_hours: int,
    apply_changes: bool,
    source_slug: str | None = None,
) -> None:
    database_url = _required("DATABASE_URL")
    now = datetime.now(ZoneInfo(timezone))
    summary = auto_review_documents(
        database_url,
        now - timedelta(hours=window_hours),
        now,
        os.getenv("AUTO_APPROVAL_POLICY_VERSION", "2026-08-pilot-v2"),
        apply_changes,
        source_slug,
    )
    print(
        "auto review finished: "
        f"candidates={summary.candidate_count} approved={summary.approved_count} "
        f"exceptions={summary.exception_count} "
        f"dismissed={getattr(summary, 'dismissed_count', 0)}"
    )


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
