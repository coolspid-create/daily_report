from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import fitz
from report_collector.domain.errors import FileValidationError


@dataclass(frozen=True)
class ValidatedPdf:
    sha256: str
    size_bytes: int
    page_count: int
    is_encrypted: bool


def validate_pdf_bytes(content: bytes, content_type: str, max_bytes: int) -> ValidatedPdf:
    if len(content) > max_bytes:
        raise FileValidationError("FILE_TOO_LARGE")
    if "html" in content_type.lower() or content.lstrip().lower().startswith(
        (b"<!doctype html", b"<html")
    ):
        raise FileValidationError("FILE_INVALID_SIGNATURE")
    if not content.startswith(b"%PDF-"):
        raise FileValidationError("FILE_INVALID_SIGNATURE")
    try:
        document = fitz.open(stream=content, filetype="pdf")
        encrypted = document.needs_pass
        pages = document.page_count
        document.close()
    except Exception as error:
        raise FileValidationError("FILE_INVALID_PDF") from error
    if encrypted:
        raise FileValidationError("FILE_ENCRYPTED")
    if pages < 1:
        raise FileValidationError("FILE_EMPTY")
    return ValidatedPdf(sha256(content).hexdigest(), len(content), pages, False)


def validate_pdf_path(path: Path, content_type: str, max_bytes: int) -> ValidatedPdf:
    return validate_pdf_bytes(path.read_bytes(), content_type, max_bytes)
