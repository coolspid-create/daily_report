import json
from collections.abc import Callable
from hashlib import sha256

from jsonschema import Draft202012Validator, FormatChecker
from report_collector.repositories.publication_repository import PublicationRepository

ArtifactBuilder = Callable[[dict[str, object]], None]


def publish_snapshot(
    snapshot: dict[str, object],
    schema: dict[str, object],
    repository: PublicationRepository,
    artifact_builder: ArtifactBuilder,
) -> str:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(snapshot)
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = sha256(canonical.encode()).hexdigest()
    artifact_builder(snapshot)
    snapshot_id = repository.stage(str(snapshot["range"]), snapshot, checksum)
    repository.activate(snapshot_id)
    return snapshot_id
