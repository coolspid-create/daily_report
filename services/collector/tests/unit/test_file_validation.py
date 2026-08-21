from base64 import b64decode
from pathlib import Path

import pytest
from report_collector.domain.errors import FileValidationError
from report_collector.services.file_validation_service import validate_pdf_bytes


def test_valid_pdf(fixture_root: Path) -> None:
    content = b64decode((fixture_root / "pdf/valid.pdf.b64").read_text(encoding="ascii"))
    result = validate_pdf_bytes(content, "application/pdf", 2_000_000)
    assert result.page_count == 1
    assert len(result.sha256) == 64


@pytest.mark.parametrize(
    ("name", "content_type", "code"),
    [
        ("corrupt.pdf", "application/pdf", "FILE_INVALID_PDF"),
        ("html-disguised.pdf", "text/html", "FILE_INVALID_SIGNATURE"),
    ],
)
def test_invalid_pdf_fixtures(fixture_root: Path, name: str, content_type: str, code: str) -> None:
    with pytest.raises(FileValidationError, match=code):
        validate_pdf_bytes((fixture_root / f"pdf/{name}").read_bytes(), content_type, 2_000_000)


def test_pdf_size_limit(fixture_root: Path) -> None:
    content = b64decode((fixture_root / "pdf/valid.pdf.b64").read_text(encoding="ascii"))
    with pytest.raises(FileValidationError, match="FILE_TOO_LARGE"):
        validate_pdf_bytes(content, "application/pdf", 10)
