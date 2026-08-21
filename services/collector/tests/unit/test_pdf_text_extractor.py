from report_collector.extractors.pdf_text_extractor import _restore_paragraph


def test_pdf_paragraph_restoration_keeps_lines_together() -> None:
    restored = _restore_paragraph("첫 문장입니다.\n둘째 문장도 이어집니다.\n\n세 번째 문단입니다.")
    assert restored == "첫 문장입니다. 둘째 문장도 이어집니다. 세 번째 문단입니다."
