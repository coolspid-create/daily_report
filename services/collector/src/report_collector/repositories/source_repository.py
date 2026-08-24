from typing import Protocol

from report_collector.domain.models import SourceDocument


class SourceRepository(Protocol):
    def get_cursor(self, source_id: str) -> str | None: ...
    def save_document(self, source_id: str, document: SourceDocument) -> tuple[str, bool] | str | None: ...
    def finish_run(
        self,
        source_id: str,
        cursor: str | None,
        discovered: int,
        failed: int,
        new_count: int | None = None,
        updated_count: int = 0,
    ) -> None: ...
    def fail_run(self, source_id: str, error_code: str, error_message: str) -> None: ...


class MemorySourceRepository:
    def __init__(self) -> None:
        self.cursors: dict[str, str] = {}
        self.documents: dict[tuple[str, str], SourceDocument] = {}
        self.runs: list[dict[str, str | int | None]] = []

    def get_cursor(self, source_id: str) -> str | None:
        return self.cursors.get(source_id)

    def save_document(self, source_id: str, document: SourceDocument) -> tuple[str, bool] | str | None:
        key = (source_id, document.source_item_key)
        is_new = key not in self.documents
        self.documents[key] = document
        return document.source_item_key, is_new

    def finish_run(
        self,
        source_id: str,
        cursor: str | None,
        discovered: int,
        failed: int,
        new_count: int | None = None,
        updated_count: int = 0,
    ) -> None:
        if cursor:
            self.cursors[source_id] = cursor
        actual_new = max(0, new_count if new_count is not None else (discovered - failed))
        self.runs.append(
            {
                "source_id": source_id,
                "cursor": cursor,
                "discovered": max(0, discovered),
                "new_count": actual_new,
                "updated_count": max(0, updated_count),
                "failed": max(0, failed),
            }
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
