from pathlib import Path

from report_collector.cli.publish_approved_command import publish_approved_command
from report_collector.cli.snapshot_command import SnapshotBuildResult


def test_publish_approved_skips_telegram_when_no_documents(monkeypatch: object, tmp_path: Path) -> None:
    empty = SnapshotBuildResult("publication", "snapshot", 0, {})
    monkeypatch.setattr(
        "report_collector.cli.publish_approved_command.snapshot_command", lambda *_: empty
    )  # type: ignore[attr-defined]
    monkeypatch.setattr(
        "report_collector.cli.publish_approved_command._deliver", lambda *_: (_ for _ in ()).throw(AssertionError())
    )  # type: ignore[attr-defined]

    assert publish_approved_command(tmp_path, "Asia/Seoul", tmp_path) is None


def test_publish_approved_delivers_new_snapshot(monkeypatch: object, tmp_path: Path) -> None:
    result = SnapshotBuildResult("publication", "snapshot", 2, {"reportsByTopic": {"all": []}})
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")  # type: ignore[attr-defined]
    monkeypatch.setattr(
        "report_collector.cli.publish_approved_command.snapshot_command", lambda *_: result
    )  # type: ignore[attr-defined]
    monkeypatch.setattr(
        "report_collector.cli.publish_approved_command._deliver", lambda *_: 1
    )  # type: ignore[attr-defined]

    assert publish_approved_command(tmp_path, "Asia/Seoul", tmp_path) == result
