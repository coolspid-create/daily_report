import importlib
from pathlib import Path

import pytest
from report_collector.cli.collect_command import CollectBatchSummary

daily = importlib.import_module("report_collector.cli.daily_publish_command")
press = importlib.import_module("report_collector.cli.press_collect_command")
collect = importlib.import_module("report_collector.cli.collect_command")


def test_reports_include_due_recovery_probes(monkeypatch):
    monkeypatch.setattr(daily, "update_automation_stage", lambda *_: None)
    monkeypatch.setattr(daily, "collect_and_summarize", lambda *_: CollectBatchSummary(0, 2, 3))
    calls = []

    def due(database_url, content_type):
        assert content_type == "REPORT"
        return {"sk-securities-research"}

    monkeypatch.setattr(daily, "load_recovery_probe_source_slugs", due)
    monkeypatch.setattr(
        daily, "collect_sources_and_summarize",
        lambda sources, *args, **kwargs: calls.append(sources) or CollectBatchSummary(0, 1, 2),
    )
    summary = daily._collect(Path("."), "unused", "run")
    assert calls == [["sk-securities-research"]]
    assert summary.new_documents_count == 3


def test_all_disabled_sources_do_not_prevent_recovery(monkeypatch):
    monkeypatch.setattr(collect, "_source_paths", lambda *_: [])
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert collect.collect_and_summarize(None, True, Path("."), Path("schema")) == (
        CollectBatchSummary(0, 0, 0)
    )


@pytest.mark.parametrize("failed,attempted", [(1, 1), (0, 0)])
def test_press_never_reports_success_for_failure_or_no_attempt(monkeypatch, failed, attempted):
    monkeypatch.setenv("DATABASE_URL", "unused")
    monkeypatch.setattr(press, "_collect", lambda *_: CollectBatchSummary(
        failed, 0, 0, ("fixture",) if failed else (), attempted,
    ))
    from types import SimpleNamespace
    monkeypatch.setattr(press, "auto_review_documents", lambda *_args, **_kw: SimpleNamespace(approved_count=0))
    monkeypatch.setattr(press, "publish_approved_command", lambda *_args, **_kw: None)
    with pytest.raises(RuntimeError):
        press.press_collect_command(Path("."), "Asia/Seoul", 168, Path("output"))


def test_successful_empty_press_run_is_not_failure(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "unused")
    monkeypatch.setattr(press, "_collect", lambda *_: CollectBatchSummary(0, 0, 0, (), 1))
    from types import SimpleNamespace
    monkeypatch.setattr(press, "auto_review_documents", lambda *_args, **_kw: SimpleNamespace(approved_count=0))
    monkeypatch.setattr(press, "publish_approved_command", lambda *_args, **_kw: None)
    press.press_collect_command(Path("."), "Asia/Seoul", 168, Path("output"))
