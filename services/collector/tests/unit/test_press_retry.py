import importlib
from pathlib import Path

from report_collector.cli.collect_command import CollectBatchSummary

press_collect_module = importlib.import_module("report_collector.cli.press_collect_command")


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

    monkeypatch.setattr(
        press_collect_module, "collect_and_summarize", lambda *_args, **_kwargs: initial
    )
    monkeypatch.setattr(
        press_collect_module, "load_retryable_press_source_slugs", lambda *_: {"press-retry"}
    )
    monkeypatch.setattr(
        press_collect_module, "load_recovery_probe_press_source_slugs", lambda *_: set()
    )
    monkeypatch.setattr(
        press_collect_module,
        "collect_sources_and_summarize",
        lambda source_ids, *_args, **kwargs: calls.append((source_ids, kwargs)) or retry,
    )
    monkeypatch.setenv("PRESS_RETRY_DELAY_SECONDS", "0")

    result = press_collect_module._collect(Path("."), "postgresql://example")

    assert calls == [(["press-retry"], {"refresh_recent": True})]
    assert result.new_documents_count == 3
    assert result.discovered_count == 11
    assert result.failed_source_ids == ("press-disabled", "press-retry", "report-source")
    assert result.failed_sources == 3


def test_collect_probes_disabled_press_sources_once_per_day(monkeypatch) -> None:
    initial = CollectBatchSummary(0, 2, 4)
    recovery = CollectBatchSummary(0, 1, 2)
    calls: list[object] = []

    monkeypatch.setattr(
        press_collect_module, "collect_and_summarize", lambda *_args, **_kwargs: initial
    )
    monkeypatch.setattr(
        press_collect_module, "load_retryable_press_source_slugs", lambda *_: set()
    )
    monkeypatch.setattr(
        press_collect_module,
        "load_recovery_probe_press_source_slugs",
        lambda *_: {"molit-press", "msit-press"},
    )
    monkeypatch.setattr(
        press_collect_module,
        "collect_sources_and_summarize",
        lambda source_ids, *_args, **kwargs: calls.append((source_ids, kwargs)) or recovery,
    )

    result = press_collect_module._collect(Path("."), "postgresql://example")

    assert calls == [(["molit-press", "msit-press"], {"refresh_recent": True})]
    assert result.new_documents_count == 3
    assert result.discovered_count == 6
