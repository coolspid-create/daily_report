from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class ExtractedText:
    text: str
    page_count: int
    ocr_required: bool
    ocr_used: bool = False


def extract_pdf_text(
    path: Path, minimum_characters: int = 200, enable_ocr: bool = False
) -> ExtractedText:
    with fitz.open(path) as document:
        pages = [_page_text(page) for page in document]
        text = "\n\n".join(part for part in pages if part)
        ocr_required = len(text) < minimum_characters
        if ocr_required and enable_ocr:
            ocr_text = "\n\n".join(_ocr_page_text(page) for page in document)
            if len(ocr_text) > len(text):
                text = ocr_text
        return ExtractedText(
            text=text,
            page_count=document.page_count,
            ocr_required=len(text) < minimum_characters,
            ocr_used=ocr_required and len(text) >= minimum_characters,
        )


def _page_text(page: fitz.Page) -> str:
    blocks = page.get_text("blocks", sort=True)
    return "\n\n".join(_restore_paragraph(block[4]) for block in blocks if block[4].strip())


def _restore_paragraph(value: str) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return " ".join(lines).replace("- ", "")


def _ocr_page_text(page: fitz.Page) -> str:
    try:
        text_page = page.get_textpage_ocr(language="kor+eng", dpi=200, full=True)
    except (RuntimeError, OSError):
        return ""
    return _restore_paragraph(page.get_text("text", textpage=text_page))
