import asyncio
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from report_collector.pipelines.build_digest import build_digest
from report_collector.pipelines.publish_snapshot import publish_snapshot
from report_collector.providers.storage.supabase_storage import SupabaseDigestStorage
from report_collector.repositories.supabase.postgres_digest_repository import (
    save_digest,
    set_publication_status,
)
from report_collector.repositories.supabase.postgres_documents import (
    ensure_publication,
    load_approved_documents,
)
from report_collector.repositories.supabase.postgres_publication_repository import (
    PostgresPublicationRepository,
)
from report_collector.services.publication_service import TOPIC_LABELS, build_snapshot


@dataclass(frozen=True)
class SnapshotBuildResult:
    publication_id: str
    snapshot_id: str
    document_count: int
    snapshot: dict[str, Any]


def _required_environment() -> tuple[str, SupabaseDigestStorage]:
    database_url = os.environ.get("DATABASE_URL")
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not database_url or not supabase_url or not service_key:
        raise SystemExit("DATABASE_URL, SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    bucket = os.environ.get("DIGEST_BUCKET", "digests")
    return database_url, SupabaseDigestStorage(supabase_url, service_key, bucket)


async def _render_digests(
    snapshot: dict[str, Any], output_dir: Path
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for topic_id in TOPIC_LABELS:
        results[topic_id] = await build_digest(snapshot, topic_id, output_dir)
    return results


def _upload_digests(
    storage: SupabaseDigestStorage,
    database_url: str,
    publication_id: str,
    rendered: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str | bool]]:
    digests: dict[str, dict[str, str | bool]] = {}
    for topic_id, metadata in rendered.items():
        path = Path(str(metadata["path"]))
        object_path = f"{publication_id}/{path.name}"
        url = storage.upload(path, object_path)
        save_digest(
            database_url,
            publication_id,
            topic_id,
            object_path,
            int(metadata["size_bytes"]),
            str(metadata["checksum"]),
        )
        digests[topic_id] = {"available": True, "url": url}
    return digests


def snapshot_command(
    date_value: str, range_key: str, schema_path: Path, output_dir: Path
) -> SnapshotBuildResult:
    database_url, storage = _required_environment()
    publication_date = date.fromisoformat(date_value)
    documents = load_approved_documents(database_url, publication_date, range_key)
    snapshot = build_snapshot(documents, publication_date, range_key)
    publication_id = ensure_publication(database_url, publication_date, range_key)
    try:
        rendered = asyncio.run(_render_digests(snapshot, output_dir))
        snapshot["digests"] = _upload_digests(
            storage, database_url, publication_id, rendered
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        repository = PostgresPublicationRepository(database_url, publication_id)
        snapshot_id = publish_snapshot(snapshot, schema, repository, lambda _: None)
        set_publication_status(database_url, publication_id, "PUBLISHED")
    except Exception:
        set_publication_status(database_url, publication_id, "FAILED")
        raise
    print(f"activated snapshot {snapshot_id} with {len(documents)} approved documents")
    return SnapshotBuildResult(publication_id, snapshot_id, len(documents), snapshot)
