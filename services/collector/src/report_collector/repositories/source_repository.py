from typing import Protocol

from report_collector.domain.models import SourceDocument


class SourceRepository(Protocol):
    def get_cursor(self, source_id: str) -> str | None: ...
    def save_document(self, source_id: str, document: SourceDocument) -> str | None: ...
    def finish_run(
        self, source_id: str, cursor: str | None, discovered: int, failed: int
    ) -> None: ...
    def fail_run(self, source_id: str, error_code: str, error_message: str) -> None: ...


class MemorySourceRepository:
    def __init__(self) -> None:
        self.cursors: dict[str, str] = {}
        self.documents: dict[tuple[str, str], SourceDocument] = {}
        self.runs: list[dict[str, str | int | None]] = []

    def get_cursor(self, source_id: str) -> str | None:
        return self.cursors.get(source_id)

    def save_document(self, source_id: str, document: SourceDocument) -> str | None:
        self.documents[(source_id, document.source_item_key)] = document
        return None

    def finish_run(self, source_id: str, cursor: str | None, discovered: int, failed: int) -> None:
        if cursor:
            self.cursors[source_id] = cursor
        self.runs.append(
            {"source_id": source_id, "cursor": cursor, "discovered": discovered, "failed": failed}
        )

    def fail_run(self, source_id: str, error_code: str, error_message: str) -> None:
        self.runs.append(
            {
                "source_id": source_id,
                "status": "FAILED",
                "error_code": error_code,
                "error_message": error_message,
            }
        )
