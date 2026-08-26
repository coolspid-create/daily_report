from report_collector.services.telegram_briefing import (
    TELEGRAM_MESSAGE_CHARACTER_LIMIT,
    build_telegram_briefing,
)


def test_briefing_uses_snapshot_links_and_digest() -> None:
    snapshot = {
        "reportsByTopic": {
            "all": [
                {
                    "title": "AI & 공공정책",
                    "publishedAt": "2026-08-22",
                    "institution": "연구원",
                    "shortSummary": "핵심 <요약>",
                    "keyTags": ["AI", "정책"],
                    "file": {
                        "downloadUrl": "https://example.org/report.pdf",
                        "sourceUrl": "https://example.org/report",
                    },
                }
            ]
        },
        "digests": {"all": {"available": True, "url": "https://example.org/digest.pdf"}},
    }
    result = build_telegram_briefing(snapshot, "2026-08-21", "https://reports.example")
    assert "AI &amp; 공공정책" in result.messages[0]
    assert "(2026.08.22)" in result.messages[0]
    assert "핵심 &lt;요약&gt;" not in result.messages[0]
    assert "AI · 정책" not in result.messages[0]
    assert "\n연구원\n" in result.messages[0]
    assert "report.pdf" in result.messages[0]
    assert '\n\n<a href="https://reports.example">오늘의 공공리포트 전체보기</a>' in result.messages[0]
    assert result.digest_url == "https://example.org/digest.pdf"


def test_briefing_omits_duplicate_source_and_pdf_link() -> None:
    url = "https://official.example/report.pdf"
    snapshot = {
        "reportsByTopic": {
            "all": [
                {
                    "title": "공식 PDF만 제공하는 자료",
                    "institution": "공식 기관",
                    "file": {"downloadUrl": url, "sourceUrl": url},
                }
            ]
        },
        "digests": {},
    }

    result = build_telegram_briefing(snapshot, "2026-08-26")

    assert result.messages[0].count(url) == 1
    assert "원문" not in result.messages[0]


def test_briefing_omits_missing_or_invalid_report_date() -> None:
    snapshot = {"reportsByTopic": {"all": [{"title": "날짜 없음", "file": {}}]}, "digests": {}}
    result = build_telegram_briefing(snapshot, "2026-08-21")
    assert "날짜 없음(" not in result.messages[0]


def test_briefing_splits_long_messages() -> None:
    report = {
        "title": "긴 보고서" * 500,
        "institution": "연구원",
        "keyTags": [],
        "file": {"sourceUrl": "https://example.org"},
    }
    snapshot = {"reportsByTopic": {"all": [report, report]}, "digests": {}}
    assert len(build_telegram_briefing(snapshot, "2026-08-21").messages) == 2


def test_briefing_keeps_a_near_limit_message_together() -> None:
    report = {
        "title": "긴 제목" * 430,
        "institution": "연구원",
        "keyTags": ["정책", "산업", "동향"],
        "file": {"sourceUrl": "https://example.org"},
    }
    snapshot = {"reportsByTopic": {"all": [report, report]}, "digests": {}}
    result = build_telegram_briefing(snapshot, "2026-08-21", "https://reports.example")
    assert len(result.messages) == 1
    assert len(result.messages[0]) <= TELEGRAM_MESSAGE_CHARACTER_LIMIT
