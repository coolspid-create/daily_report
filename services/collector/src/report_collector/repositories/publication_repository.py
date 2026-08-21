from copy import deepcopy
from typing import Protocol
from uuid import uuid4


class PublicationRepository(Protocol):
    def stage(self, range_key: str, snapshot: dict[str, object], checksum: str) -> str: ...
    def activate(self, snapshot_id: str) -> None: ...


class MemoryPublicationRepository:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict[str, object]] = {}
        self.current: dict[str, str] = {}

    def stage(self, range_key: str, snapshot: dict[str, object], checksum: str) -> str:
        snapshot_id = str(uuid4())
        self.snapshots[snapshot_id] = {
            "range": range_key,
            "snapshot": deepcopy(snapshot),
            "checksum": checksum,
        }
        return snapshot_id

    def activate(self, snapshot_id: str) -> None:
        record = self.snapshots[snapshot_id]
        self.current[str(record["range"])] = snapshot_id

    def current_payload(self, range_key: str) -> dict[str, object] | None:
        snapshot_id = self.current.get(range_key)
        return deepcopy(self.snapshots[snapshot_id]["snapshot"]) if snapshot_id else None  # type: ignore[return-value]
