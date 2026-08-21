import json
from base64 import b64decode
from pathlib import Path

import pytest
from pydantic import HttpUrl
from report_collector.domain.enums import RightsStatus
from report_collector.domain.models import Attachment, SourceDocument
from report_collector.pipelines import process_source_document as process_module
from report_collector.pipelines.process_source_document import SourceDocumentProcessor
from report_collector.providers.http.http_client import DownloadedFile


class FixtureHttp:
    def __init__(self, content: bytes) -> None:
        self.content = content

    async def fetch(self, url: str, max_bytes: int) -> DownloadedFile:
        return DownloadedFile(self.content, "application/pdf", url)


class RetryingFixtureHttp(FixtureHttp):
    def __init__(self, content: bytes) -> None:
        super().__init__(content)
        self.calls = 0

    async def fetch(self, url: str, max_bytes: int) -> DownloadedFile:
        self.calls += 1
        if self.calls == 1:
            raise OSError("temporary download failure")
        return await super().fetch(url, max_bytes)


@pytest.mark.asyncio
async def test_valid_source_pdf_reaches_review_processing(
    fixture_root: Path,
    contract_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[tuple] = []
    content = b64decode((fixture_root / "pdf/valid.pdf.b64").read_text(encoding="ascii"))
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text())
    processor = SourceDocumentProcessor(
        "postgresql://fixture", FixtureHttp(content), tmp_path, 2_000_000, 48, schema  # type: ignore[arg-type]
    )
    document = SourceDocument(
        source_item_key="fixture-1",
        title="AI 경제 보고서",
        institution="가상 기관",
        detail_url=HttpUrl("https://example.com/report/1"),
        attachments=[
            Attachment(
                url=HttpUrl("https://example.com/report.pdf"),
                file_name="report.pdf",
                declared_type="application/pdf",
            )
        ],
        rights_status=RightsStatus.LINK_ONLY,
    )
    monkeypatch.setattr(process_module, "save_processing_result", lambda *args: saved.append(args))
    await processor.process("document-id", document)
    assert saved
    assert saved[0][4].page_count == 1
    assert saved[0][2].topic_candidates[0] == "ai-tech"


@pytest.mark.asyncio
async def test_source_pdf_processing_retries_transient_failure(
    fixture_root: Path,
    contract_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[tuple] = []
    content = b64decode((fixture_root / "pdf/valid.pdf.b64").read_text(encoding="ascii"))
    http = RetryingFixtureHttp(content)
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text())
    processor = SourceDocumentProcessor(
        "postgresql://fixture", http, tmp_path, 2_000_000, 48, schema, 2  # type: ignore[arg-type]
    )
    document = SourceDocument(
        source_item_key="fixture-retry",
        title="AI 경제 보고서",
        institution="가상 기관",
        detail_url=HttpUrl("https://example.com/report/2"),
        attachments=[
            Attachment(
                url=HttpUrl("https://example.com/report.pdf"),
                file_name="report.pdf",
                declared_type="application/pdf",
            )
        ],
        rights_status=RightsStatus.LINK_ONLY,
    )
    monkeypatch.setattr(process_module, "save_processing_result", lambda *args: saved.append(args))
    await processor.process("document-id", document)
    assert http.calls == 2
    assert saved
