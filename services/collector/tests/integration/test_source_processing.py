import json
from base64 import b64decode
from pathlib import Path

import pytest
from pydantic import HttpUrl
from report_collector.domain.enums import RightsStatus
from report_collector.domain.models import AnalysisResult, Attachment, SourceDocument
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


class PdfEvidenceFailureSummarizer:
    async def summarize(self, request: object) -> AnalysisResult:
        if getattr(request, "page_count", None):
            raise ValueError("evidence page exceeds document page count")
        return AnalysisResult(
            why_it_matters="공식 상세페이지의 요약을 바탕으로 핵심 쟁점을 정리했습니다.",
            summary_kind="ANALYZED",
            key_points=["일본 코스닥시장 세그먼트 개편 사례를 분석합니다."],
            key_tags=["코스닥", "세그먼트"],
            topic_candidates=["economy"],
            content_tag="공식 본문 분석",
            confidence=0.82,
            evidence_pages=[],
        )


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


@pytest.mark.asyncio
async def test_public_html_summary_is_analyzed_without_a_pdf(
    contract_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[tuple] = []
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text())
    processor = SourceDocumentProcessor(
        "postgresql://fixture", FixtureHttp(b""), tmp_path, 2_000_000, 48, schema  # type: ignore[arg-type]
    )
    document = SourceDocument(
        source_item_key="kotra-html",
        title="칠레 푸드테크 시장 동향",
        institution="KOTRA 해외시장뉴스",
        detail_url=HttpUrl("https://example.com/news/1"),
        official_summary=(
            "칠레 푸드테크 시장은 대체 단백질과 식품 유통 기술을 중심으로 성장하고 있습니다. "
            "현지 기업은 지속가능한 식품 생산을 위해 해외 기술 협력과 투자 유치에 나서고 있습니다."
        ),
        rights_status=RightsStatus.LINK_ONLY,
    )
    monkeypatch.setattr(process_module, "save_processing_result", lambda *args: saved.append(args))
    await processor.process("document-id", document)
    assert saved[0][2].summary_kind == "ANALYZED"
    assert "푸드테크" in saved[0][2].why_it_matters


@pytest.mark.asyncio
async def test_pdf_evidence_failure_falls_back_to_official_summary(
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
    processor.summarizer = PdfEvidenceFailureSummarizer()  # type: ignore[assignment]
    document = SourceDocument(
        source_item_key="kif-1",
        title="코스닥시장 세그먼트 개편",
        institution="한국금융연구원",
        detail_url=HttpUrl("https://example.com/report/3"),
        official_summary="일본의 시장구분 재편 사례와 국내 코스닥시장에 주는 시사점을 분석합니다.",
        attachments=[Attachment(
            url=HttpUrl("https://example.com/report.pdf"),
            file_name="report.pdf",
            declared_type="application/pdf",
        )],
        rights_status=RightsStatus.LINK_ONLY,
    )
    monkeypatch.setattr(process_module, "save_processing_result", lambda *args: saved.append(args))
    await processor.process("document-id", document)
    assert saved[0][2].summary_kind == "ANALYZED"
    assert saved[0][2].content_tag == "공식 본문 분석"
