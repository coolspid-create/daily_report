import asyncio
import importlib
from pathlib import Path

import pytest
from report_collector.pipelines.collect_source import CollectionResult
from report_collector.pipelines.source_run_guard import run_with_source_timeout
from report_collector.repositories.source_repository import MemorySourceRepository

collect_command_module = importlib.import_module("report_collector.cli.collect_command")


@pytest.mark.asyncio
async def test_timeout_is_recorded_as_a_failed_source_run() -> None:
    repository = MemorySourceRepository()

    result = await run_with_source_timeout(
        "fixture", repository, 1, asyncio.sleep(2, result=CollectionResult("fixture", 0, 0, None))
    )

    assert result.failed == 1
    assert repository.runs[-1]["status"] == "FAILED"
    assert repository.runs[-1]["error_code"] == "SOURCE_TIMEOUT"


@pytest.mark.asyncio
async def test_exception_is_recorded_and_returns_a_failure_result() -> None:
    repository = MemorySourceRepository()

    async def fail() -> CollectionResult:
        raise RuntimeError("public page unavailable")

    result = await run_with_source_timeout("fixture", repository, 30, fail())

    assert result.failed == 1
    assert repository.runs[-1]["error_code"] == "SOURCE_ERROR"


def test_collection_continues_after_source_initialization_error(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    async def fake_run_source(path: Path, *_: object) -> int:
        calls.append(path.stem)
        if path.stem == "first":
            raise RuntimeError("configuration unavailable")
        return 0

    async def no_browser(*_: object) -> None:
        return None

    monkeypatch.setattr(collect_command_module, "run_source", fake_run_source)
    monkeypatch.setattr(collect_command_module, "_start_shared_browser", no_browser)
    monkeypatch.setattr(collect_command_module, "_source_host", lambda *_: "fixture.test")
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    first.touch()
    second.touch()
    monkeypatch.setattr(
        collect_command_module,
        "_source_paths",
        lambda *_: [first, second],
    )

    collect_command_module.collect_command(None, True, Path("config"), Path("schema.json"))

    assert set(calls) == {"first", "second"}


def test_collection_limits_parallel_sources(monkeypatch, tmp_path: Path) -> None:
    active = 0
    peak = 0

    async def fake_run_source(*_: object) -> int:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return 0

    async def no_browser(*_: object) -> None:
        return None

    paths = [tmp_path / f"source-{index}.yaml" for index in range(4)]
    for path in paths:
        path.touch()
    monkeypatch.setattr(collect_command_module, "run_source", fake_run_source)
    monkeypatch.setattr(collect_command_module, "_start_shared_browser", no_browser)
    monkeypatch.setattr(collect_command_module, "_source_paths", lambda *_: paths)
    monkeypatch.setattr(collect_command_module, "_source_host", lambda path, _: path.stem)
    monkeypatch.setenv("MAX_SOURCE_CONCURRENCY", "2")

    assert collect_command_module.collect_command(None, True, Path("config"), Path("schema.json")) == 0
    assert peak == 2


def test_collection_summary_keeps_failed_source_ids(monkeypatch, tmp_path: Path) -> None:
    async def fake_run_source(path: Path, *_: object) -> CollectionResult:
        return CollectionResult(path.stem, 0, int(path.stem == "failed"), None)

    async def no_browser(*_: object) -> None:
        return None

    paths = [tmp_path / "healthy.yaml", tmp_path / "failed.yaml"]
    for path in paths:
        path.touch()
    monkeypatch.setattr(collect_command_module, "run_source", fake_run_source)
    monkeypatch.setattr(collect_command_module, "_start_shared_browser", no_browser)
    monkeypatch.setattr(collect_command_module, "_source_host", lambda path, _: path.stem)

    summary = collect_command_module.collect_sources_and_summarize(
        ["healthy", "failed"], tmp_path, Path("schema.json")
    )

    assert summary.failed_sources == 1
    assert summary.failed_source_ids == ("failed",)
