from datetime import datetime
from zoneinfo import ZoneInfo

from report_collector.cli.daily_publish_command import _scheduled_slot

SEOUL = ZoneInfo("Asia/Seoul")


def test_early_manual_run_uses_previous_daily_slot() -> None:
    now = datetime(2026, 8, 22, 1, 12, tzinfo=SEOUL)

    assert _scheduled_slot(now) == datetime(2026, 8, 21, 8, 35, tzinfo=SEOUL)


def test_run_after_schedule_uses_current_daily_slot() -> None:
    now = datetime(2026, 8, 22, 8, 36, tzinfo=SEOUL)

    assert _scheduled_slot(now) == datetime(2026, 8, 22, 8, 35, tzinfo=SEOUL)
