import asyncio
from pathlib import Path
from uuid import uuid4

from report_collector.domain.errors import FileValidationError
from report_collector.domain.models import (
    AnalysisRequest,
    AnalysisResult,
    Attachment,
    SourceDocument,
)
from report_collector.extractors.pdf_text_extractor import ExtractedText, extract_pdf_text
from report_collector.providers.ai.provider_factory import build_analysis_provider
from report_collector.providers.http.http_client import PublicHttpClient
from report_collector.repositories.supabase.postgres_processing_repository import (
    mark_file_invalid,
    save_processing_result,
)
from report_collector.services.file_validation_service import ValidatedPdf, validate_pdf_bytes
from report_collector.services.summarization_service import SummarizationService


def _tag_if_press(analysis: AnalysisResult, document: SourceDocument) -> AnalysisResult:
    if "보도자료" in document.institution or "금융위원회" in document.institution:
        return analysis.model_copy(update={"content_tag": "보도자료"})
    return analysis


class SourceDocumentProcessor:
    def __init__(
        self,
        database_url: str,
        http: PublicHttpClient,
        temporary_root: Path,
        max_bytes: int,
        ttl_hours: int,
        analysis_schema: dict[str, object],
        pdf_processing_attempts: int = 3,
        pdf_ocr_enabled: bool = False,
    ) -> None:
        self.database_url = database_url
        self.http = http
        self.temporary_root = temporary_root
        self.max_bytes = max_bytes
        self.ttl_hours = ttl_hours
        self.pdf_processing_attempts = pdf_processing_attempts
        self.pdf_ocr_enabled = pdf_ocr_enabled
        self.summarizer = SummarizationService(build_analysis_provider(), analysis_schema)

    @staticmethod
    def _pdf_attachment(document: SourceDocument) -> Attachment | None:
        return next(
            (
                item
                for item in document.attachments
                if item.file_name.lower().endswith(".pdf")
                or item.declared_type == "application/pdf"
            ),
            None,
        )

    async def _title_analysis(self, document: SourceDocument) -> AnalysisResult:
        return await self.summarizer.summarize(
            AnalysisRequest(
                title=document.title,
                institution=document.institution,
                text=f"{document.title}. 공식 출처에서 원문을 확인해야 합니다.",
            )
        )

    async def _official_summary_analysis(self, document: SourceDocument) -> AnalysisResult | None:
        if not document.official_summary:
            return None
        request = AnalysisRequest(
            title=document.title,
            institution=document.institution,
            text=document.official_summary,
        )
        result = await self.summarizer.summarize(request)
        if result.summary_kind == "UNAVAILABLE" and len(document.official_summary) >= 400:
            result = await self.summarizer.summarize(request)
        if result.summary_kind == "UNAVAILABLE":
            return None
        return result.model_copy(update={"content_tag": "공식 본문 분석"})

    async def _download_and_extract(
        self, document_id: str, file_url: str
    ) -> tuple[ValidatedPdf, Path, ExtractedText]:
        last_error: Exception | None = None
        for attempt in range(self.pdf_processing_attempts):
            try:
                downloaded = await self.http.fetch(file_url, self.max_bytes + 1)
                validation = validate_pdf_bytes(
                    downloaded.content, downloaded.content_type, self.max_bytes
                )
                self.temporary_root.mkdir(parents=True, exist_ok=True)
                path = self.temporary_root / f"{document_id}-{uuid4().hex}.pdf"
                path.write_bytes(downloaded.content)
                extracted = extract_pdf_text(path, enable_ocr=self.pdf_ocr_enabled)
                return validation, path, extracted
            except FileValidationError:
                raise
            except (OSError, RuntimeError, ValueError) as error:
                last_error = error
                if attempt + 1 < self.pdf_processing_attempts:
                    await asyncio.sleep(attempt + 1)
        assert last_error is not None
        raise last_error

    async def process(self, document_id: str, document: SourceDocument) -> None:
        attachment = self._pdf_attachment(document)
        if not attachment:
            official_analysis = await self._official_summary_analysis(document)
            analysis = official_analysis or await self._title_analysis(document)
            analysis = _tag_if_press(analysis, document)
            save_processing_result(
                self.database_url, document_id, analysis, None, None, None, self.ttl_hours
            )
            return
        file_url = str(attachment.url)
        try:
            validation, path, extracted = await self._download_and_extract(document_id, file_url)
        except FileValidationError:
            mark_file_invalid(self.database_url, document_id, file_url)
            analysis = await self._official_summary_analysis(document) or await self._title_analysis(document)
            analysis = _tag_if_press(analysis, document)
            save_processing_result(
                self.database_url, document_id, analysis, None, None, None, self.ttl_hours
            )
            return
        except (OSError, RuntimeError, ValueError):
            analysis = await self._official_summary_analysis(document) or await self._title_analysis(document)
            analysis = _tag_if_press(analysis, document)
            save_processing_result(
                self.database_url, document_id, analysis, None, None, None, self.ttl_hours
            )
            return

        official_analysis = await self._official_summary_analysis(document)
        try:
            analysis = await self.summarizer.summarize(
                AnalysisRequest(
                    title=document.title,
                    institution=document.institution,
                    text=extracted.text,
                    page_count=extracted.page_count,
                )
            )
        except ValueError:
            analysis = official_analysis or await self._title_analysis(document)
        analysis = _tag_if_press(analysis, document)
        save_processing_result(
            self.database_url,
            document_id,
            analysis,
            file_url,
            validation,
            path,
            self.ttl_hours,
        )

