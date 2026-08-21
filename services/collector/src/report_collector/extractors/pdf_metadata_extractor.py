from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class PdfMetadata:
    page_count: int
    title: str | None
    author: str | None


def extract_pdf_metadata(path: Path) -> PdfMetadata:
    with fitz.open(path) as document:
        metadata = document.metadata
        return PdfMetadata(
            document.page_count, metadata.get("title") or None, metadata.get("author") or None
        )
