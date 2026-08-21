import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from report_collector.cli.collect_command import collect_command
from report_collector.cli.snapshot_command import SnapshotBuildResult, snapshot_command
from report_collector.pipelines.auto_review_documents import (
    AutoReviewSummary,
    auto_review_documents,
)
from report_collector.pipelines.daily_publication import run_daily_publication
from report_collector.pipelines.deliver_publication import deliver_publication
from report_collector.providers.notifications.telegram_provider import (
    TelegramNotificationProvider,
)
from report_collector.repositories.supabase.postgres_automation_runs import (
    AutomationAlreadyCompleted,
    finish_automation_run,
    start_automation_run,
    update_automation_stage,
)
from report_collector.repositories.supabase.postgres_documents import load_approved_documents
from report_collector.repositories.supabase.postgres_telegram_delivery import (
    load_pending_telegram_deliveries,
)


def daily_publish_command(
    root: Path, timezone: str, window_hours: int, output_dir: Path, dry_run: bool
) -> None:
    database_url = _required("DATABASE_URL")
    now = datetime.now(ZoneInfo(timezone))
    window_start = now - timedelta(hours=window_hours)
    scheduled_for = now.replace(hour=8, minute=35, second=0, microsecond=0)
    try:
        run = start_automation_run(database_url, scheduled_for, window_start, now)
    except AutomationAlreadyCompleted:
        print("daily publication already completed for this schedule")
        return
    enabled = _enabled("AUTO_APPROVAL_ENABLED") and not dry_run
    counts = {"collected": 0, "approved": 0, "exceptions": 0, "published": 0, "telegram": 0}
    try:
        if _enabled("TELEGRAM_ENABLED") and not dry_run:
            _retry_pending_deliveries(database_url)
        outcome = run_daily_publication(
            collect=lambda: _collect(root, database_url, run.run_id),
            auto_review=lambda: _auto_review(database_url, run.run_id, window_start, now, enabled),
            publish=lambda: _publish(root, run.run_id, now, output_dir),
            deliver=lambda result: _deliver_with_stage(
                database_url, run.run_id, result, now.date().isoformat()
            ),
            dry_run=not enabled,
        )
        counts.update(
            collected=outcome.review.candidate_count,
            approved=outcome.review.approved_count,
            exceptions=outcome.review.exception_count,
            published=outcome.publication.document_count if outcome.publication else 0,
            telegram=outcome.telegram_count,
        )
        finish_automation_run(database_url, run.run_id, outcome.status, counts)
        print(f"daily publication finished: {outcome.status} {counts}")
    except Exception as error:
        finish_automation_run(database_url, run.run_id, "FAILED", counts, str(error)[:1000])
        raise


def _collect(root: Path, database_url: str, run_id: str) -> int:
    update_automation_stage(database_url, run_id, "COLLECTING")
    return collect_command(
        None,
        True,
        root / "config/sources",
        root / "contracts/source-config.schema.json",
        True,
    )


def _auto_review(
    database_url: str, run_id: str, start: datetime, end: datetime, enabled: bool
) -> AutoReviewSummary:
    update_automation_stage(database_url, run_id, "AUTO_REVIEW")
    return auto_review_documents(
        database_url,
        start,
        end,
        os.getenv("AUTO_APPROVAL_POLICY_VERSION", "2026-08-v1"),
        enabled,
    )


def _publish(root: Path, run_id: str, now: datetime, output_dir: Path) -> SnapshotBuildResult:
    database_url = _required("DATABASE_URL")
    update_automation_stage(database_url, run_id, "PUBLISHING")
    documents = load_approved_documents(database_url, now.date(), "7d")
    if not documents:
        return SnapshotBuildResult("", "", 0, {})
    schema = root / "contracts/public-feed.schema.json"
    return snapshot_command(now.date().isoformat(), "7d", schema, output_dir)


def _deliver(database_url: str, result: SnapshotBuildResult, date_value: str) -> int:
    if not _enabled("TELEGRAM_ENABLED"):
        return 0
    provider = TelegramNotificationProvider(
        _required("TELEGRAM_BOT_TOKEN"),
        _required("TELEGRAM_CHAT_ID"),
        int(os.getenv("TELEGRAM_MAX_ATTEMPTS", "3")),
    )
    return deliver_publication(
        database_url,
        result.publication_id,
        date_value,
        result.snapshot,
        os.getenv("TELEGRAM_DESTINATION_KEY", "daily-report-main"),
        provider,
        os.getenv("PUBLIC_WEB_URL"),
    )


def _deliver_with_stage(
    database_url: str, run_id: str, result: SnapshotBuildResult, date_value: str
) -> int:
    update_automation_stage(database_url, run_id, "DELIVERING")
    return _deliver(database_url, result, date_value)


def _retry_pending_deliveries(database_url: str) -> None:
    provider = TelegramNotificationProvider(
        _required("TELEGRAM_BOT_TOKEN"),
        _required("TELEGRAM_CHAT_ID"),
        int(os.getenv("TELEGRAM_MAX_ATTEMPTS", "3")),
    )
    for pending in load_pending_telegram_deliveries(database_url):
        deliver_publication(
            database_url,
            pending.publication_id,
            pending.publication_date.isoformat(),
            pending.snapshot,
            pending.destination_key,
            provider,
            os.getenv("PUBLIC_WEB_URL"),
        )


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() in {"1", "true", "yes", "on"}


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
