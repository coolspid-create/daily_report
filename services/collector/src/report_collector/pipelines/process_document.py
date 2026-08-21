from dataclasses import dataclass
from pathlib import Path

from report_collector.domain.enums import DeliveryMode, ProcessingState, RightsStatus
from report_collector.extractors.pdf_text_extractor import ExtractedText, extract_pdf_text
from report_collector.services.file_validation_service import ValidatedPdf, validate_pdf_path
from report_collector.services.rights_service import choose_delivery
from report_collector.services.workflow_service import transition


@dataclass(frozen=True)
class ProcessedDocument:
    validation: ValidatedPdf
    extracted: ExtractedText
    delivery_mode: DeliveryMode
    final_state: ProcessingState


def process_pdf(
    path: Path, content_type: str, max_bytes: int, rights: RightsStatus, enable_ocr: bool = False
) -> ProcessedDocument:
    state = transition(ProcessingState.FILE_DOWNLOADED, ProcessingState.FILE_VALIDATED)
    validation = validate_pdf_path(path, content_type, max_bytes)
    extracted = extract_pdf_text(path, enable_ocr=enable_ocr)
    state = transition(
        state,
        ProcessingState.OCR_REQUIRED if extracted.ocr_required else ProcessingState.TEXT_EXTRACTED,
    )
    state = transition(state, ProcessingState.DEDUPLICATED)
    delivery = choose_delivery(
        rights,
        official_file_stable=True,
        session_dependent=False,
        mirrored_file_exists=False,
        source_available=True,
    )
    return ProcessedDocument(validation, extracted, delivery, state)
