from datetime import datetime
from zoneinfo import ZoneInfo

from report_collector.cli.daily_publish_command import (
    _deliver_no_content_notice,
    _run_key,
    _scheduled_slot,
)

SEOUL = ZoneInfo("Asia/Seoul")


def test_early_manual_run_uses_previous_daily_slot() -> None:
    now = datetime(2026, 8, 22, 1, 12, tzinfo=SEOUL)

    assert _scheduled_slot(now) == datetime(2026, 8, 21, 8, 35, tzinfo=SEOUL)


def test_run_after_schedule_uses_current_daily_slot() -> None:
    now = datetime(2026, 8, 22, 8, 36, tzinfo=SEOUL)

    assert _scheduled_slot(now) == datetime(2026, 8, 22, 8, 35, tzinfo=SEOUL)


def test_manual_run_uses_its_own_idempotency_key() -> None:
    now = datetime(2026, 8, 22, 1, 12, 34, tzinfo=SEOUL)

    assert _run_key(now, scheduled_run=False) == now


def test_scheduled_run_uses_daily_idempotency_key() -> None:
    now = datetime(2026, 8, 22, 8, 36, tzinfo=SEOUL)

    assert _run_key(now, scheduled_run=True) == datetime(2026, 8, 22, 8, 35, tzinfo=SEOUL)


def test_no_content_notice_includes_the_public_archive_link(monkeypatch: object) -> None:
    sent: list[str] = []

    class Provider:
        def __init__(self, *_: object) -> None:
            pass

        def send_message(self, message: str) -> str:
            sent.append(message)
            return "1"

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")  # type: ignore[attr-defined]
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")  # type: ignore[attr-defined]
    monkeypatch.setenv("PUBLIC_WEB_URL", "https://example.com")  # type: ignore[attr-defined]
    monkeypatch.setattr(
        "report_collector.cli.daily_publish_command.TelegramNotificationProvider", Provider
    )  # type: ignore[attr-defined]

    assert _deliver_no_content_notice(datetime(2026, 8, 22, 8, 35, tzinfo=SEOUL), 3) == 1
    assert "오늘 발행할 신규 리포트가 없습니다" in sent[0]
    assert "수집 후보 3건" in sent[0]
    assert "https://example.com" in sent[0]
