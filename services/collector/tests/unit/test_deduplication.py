from datetime import date

from report_collector.services.deduplication_service import (
    DuplicateCandidate,
    duplicate_reason,
    normalize_title,
)


def candidate(**changes) -> DuplicateCandidate:
    values = {
        "document_id": "a",
        "detail_url": "https://official.example/report/1",
        "file_url": None,
        "sha256": None,
        "title": "[기관] 2026 경제 전망.pdf",
        "institution": "공공연구원",
        "published_at": date(2026, 8, 21),
    }
    values.update(changes)
    return DuplicateCandidate(**values)


def test_normalized_title_keeps_year() -> None:
    assert normalize_title("[기관] 2026  경제-전망.pdf") == "2026 경제 전망"


def test_url_hash_and_title_duplicate_rules() -> None:
    original = candidate()
    assert (
        duplicate_reason(original, candidate(detail_url="https://official.example/report/1/"))
        == "URL_EXACT"
    )
    unrelated = candidate(
        detail_url="https://other.example/x", sha256="a" * 64, title="환경 정책 동향"
    )
    assert duplicate_reason(original, unrelated) is None
    hashed = candidate(detail_url="https://other.example/a", sha256="b" * 64)
    assert (
        duplicate_reason(hashed, candidate(detail_url="https://other.example/b", sha256="b" * 64))
        == "HASH_EXACT"
    )
    assert (
        duplicate_reason(
            original, candidate(detail_url="https://other.example/c", title="2026 경제 전망")
        )
        == "TITLE_DATE_INSTITUTION_EXACT"
    )
