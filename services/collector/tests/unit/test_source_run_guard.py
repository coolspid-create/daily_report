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

    async def fake_run_source(path: Path, *_: object) -> None:
        calls.append(path.stem)
        if path.stem == "first":
            raise RuntimeError("configuration unavailable")

    monkeypatch.setattr(collect_command_module, "run_source", fake_run_source)
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

    assert calls == ["first", "second"]
