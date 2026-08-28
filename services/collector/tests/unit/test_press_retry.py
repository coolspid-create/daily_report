import importlib
from pathlib import Path

from report_collector.cli.collect_command import CollectBatchSummary

daily_publish_module = importlib.import_module("report_collector.cli.daily_publish_command")


def test_collect_retries_only_degraded_press_sources(monkeypatch) -> None:
    initial = CollectBatchSummary(
        failed_sources=3,
        new_documents_count=2,
        discovered_count=8,
        failed_source_ids=("report-source", "press-retry", "press-disabled"),
    )
    retry = CollectBatchSummary(
        failed_sources=1,
        new_documents_count=1,
        discovered_count=3,
        failed_source_ids=("press-retry",),
    )
    calls: list[object] = []

    monkeypatch.setattr(daily_publish_module, "update_automation_stage", lambda *_: None)
    monkeypatch.setattr(daily_publish_module, "collect_and_summarize", lambda *_: initial)
    monkeypatch.setattr(
        daily_publish_module, "load_retryable_press_source_slugs", lambda *_: {"press-retry"}
    )
    monkeypatch.setattr(
        daily_publish_module,
        "collect_sources_and_summarize",
        lambda source_ids, *_args, **kwargs: calls.append((source_ids, kwargs)) or retry,
    )
    monkeypatch.setenv("PRESS_RETRY_DELAY_SECONDS", "0")

    result = daily_publish_module._collect(Path("."), "postgresql://example", "run-id")

    assert calls == [(["press-retry"], {"refresh_recent": True})]
    assert result.new_documents_count == 3
    assert result.discovered_count == 11
    assert result.failed_source_ids == ("press-disabled", "press-retry", "report-source")
    assert result.failed_sources == 3
