import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from report_collector.cli.snapshot_command import SnapshotBuildResult, snapshot_command
from report_collector.pipelines.deliver_publication import deliver_publication
from report_collector.providers.notifications.telegram_provider import TelegramNotificationProvider


def publish_approved_command(
    root: Path, timezone: str, output_dir: Path, deliver: bool = True
) -> SnapshotBuildResult | None:
    now = datetime.now(ZoneInfo(timezone))
    result = snapshot_command(
        now.date().isoformat(),
        "7d",
        root / "contracts/public-feed.schema.json",
        output_dir,
    )
    if result.document_count == 0:
        print("approved publication refresh skipped: no unpublished approved documents")
        return None
    delivery_count = _deliver(result, now.date().isoformat()) if deliver and _enabled("TELEGRAM_ENABLED") else 0
    print(f"approved publication refresh finished: documents={result.document_count} telegram={delivery_count}")
    return result


def _deliver(result: SnapshotBuildResult, publication_date: str) -> int:
    provider = TelegramNotificationProvider(
        _required("TELEGRAM_BOT_TOKEN"),
        _required("TELEGRAM_CHAT_ID"),
        int(os.getenv("TELEGRAM_MAX_ATTEMPTS", "3")),
    )
    return deliver_publication(
        _required("DATABASE_URL"),
        result.publication_id,
        publication_date,
        result.snapshot,
        f"daily-report-review-{publication_date}",
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
