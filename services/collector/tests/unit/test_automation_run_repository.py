from datetime import UTC, datetime
from typing import Any

import pytest
from report_collector.repositories.supabase import postgres_automation_runs as runs


class FakeCursor:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self._row = row

    def fetchone(self) -> dict[str, Any] | None:
        return self._row


class FakeConnection:
    def __init__(self, rows: list[dict[str, Any] | None]) -> None:
        self.rows = rows
        self.queries: list[str] = []

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, _params: object = None) -> FakeCursor:
        self.queries.append(" ".join(query.split()))
        row = self.rows.pop(0) if self.rows else None
        return FakeCursor(row)


def test_start_run_cleans_stale_runs_and_blocks_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection([None, None, {"id": "run-1", "status": "RUNNING"}])
    monkeypatch.setattr(runs.psycopg, "connect", lambda *_args, **_kwargs: connection)
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)

    with pytest.raises(runs.AutomationAlreadyRunning):
        runs.start_automation_run("postgresql://unused", now, now, now)

    assert "error_code='STALE_RUN'" in connection.queries[0]
    assert "interval '2 hours'" in connection.queries[0]


def test_start_run_returns_inserted_run(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection([None, {"id": "run-2"}])
    monkeypatch.setattr(runs.psycopg, "connect", lambda *_args, **_kwargs: connection)
    now = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)

    result = runs.start_automation_run("postgresql://unused", now, now, now)

    assert result.run_id == "run-2"
