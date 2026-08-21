import asyncio
import json
import os
from pathlib import Path
from typing import Any

from report_collector.pipelines.build_digest import build_digest
from report_collector.repositories.supabase.postgres_documents import load_current_snapshot


def _load_snapshot(range_key: str, snapshot_file: Path | None) -> dict[str, Any]:
    if snapshot_file:
        payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
        snapshot = payload.get(range_key, payload)
        if not isinstance(snapshot, dict):
            raise SystemExit("snapshot file does not contain an object")
        return snapshot
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL or --snapshot-file is required")
    return load_current_snapshot(database_url, range_key)


def digest_command(
    date: str, topic: str, range_key: str, output_dir: Path, snapshot_file: Path | None
) -> None:
    snapshot = _load_snapshot(range_key, snapshot_file)
    if str(snapshot.get("generatedAt", ""))[:10] != date:
        raise SystemExit("--date does not match snapshot generatedAt")
    result = asyncio.run(build_digest(snapshot, topic, output_dir))
    print(f"created {result['path']} ({result['size_bytes']} bytes)")
