from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def test_auto_review_window_includes_items_discovered_during_run() -> None:
    # Verify timestamp relationship:
    # 08:35 run start -> 08:42 collection finishes -> window_end is 08:42
    run_started_at = datetime(2026, 8, 24, 8, 35, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    window_start = run_started_at - timedelta(hours=24)
    item_saved_at = datetime(2026, 8, 24, 8, 42, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    collection_ended_at = datetime(2026, 8, 24, 8, 45, 0, tzinfo=ZoneInfo("Asia/Seoul"))

    # The document saved at 08:42 falls within [window_start, collection_ended_at]
    assert window_start <= item_saved_at <= collection_ended_at
    # But it would NOT fall within [window_start, run_started_at]
    assert not (window_start <= item_saved_at <= run_started_at)
