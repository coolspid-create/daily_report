import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from report_collector.digest.digest_builder import build_digest_html
from report_collector.digest.digest_view_model import build_digest_view_model
from report_collector.services.cleanup_service import cleanup_expired_files


def test_cleanup_removes_only_expired_files(tmp_path: Path) -> None:
    old = tmp_path / "old.pdf"
    fresh = tmp_path / "fresh.pdf"
    old.write_bytes(b"old")
    fresh.write_bytes(b"fresh")
    now = datetime.now(UTC)
    old_time = (now - timedelta(hours=49)).timestamp()
    os.utime(old, (old_time, old_time))
    assert cleanup_expired_files(tmp_path, 48, now) == [old]
    assert fresh.exists()


def test_digest_contains_official_links() -> None:
    snapshot = {
        "generatedAt": "2026-08-21T00:00:00+00:00",
        "topics": [{"id": "all", "label": "전체"}],
        "reportsByTopic": {
            "all": [
                {
                    "title": "보고서",
                    "institution": "기관",
                    "publishedAt": "2026-08-21",
                    "contentTag": "분석",
                    "shortSummary": "중요합니다.",
                    "keyTags": ["핵심"],
                    "file": {"sourceUrl": "https://official.example/report", "downloadUrl": None},
                }
            ]
        },
    }
    view = build_digest_view_model(snapshot, "all")
    templates = Path(__file__).resolve().parents[2] / "src/report_collector/digest/templates"
    html = build_digest_html(view, templates)
    assert "https://official.example/report" in html
    assert "원본 PDF 병합" not in html
