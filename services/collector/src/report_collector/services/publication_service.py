from datetime import UTC, date, datetime
from typing import Any

from report_collector.domain.enums import DeliveryMode, WorkflowStatus
from report_collector.domain.models import PublicationDocument
from report_collector.services.ranking_service import rank_documents

TOPIC_LABELS = {
    "all": "전체",
    "economy": "경제·금융",
    "industry": "산업·통상",
    "ai-tech": "AI·과학기술",
    "labor-welfare": "노동·복지",
    "education-population": "교육·인구",
    "land-environment": "국토·환경",
    "law-security": "법·외교·안보",
}


def _limited(documents: list[PublicationDocument], limit: int) -> list[PublicationDocument]:
    return documents[:limit]


def _report(document: PublicationDocument, publication_date: date) -> dict[str, Any]:
    return {
        "id": document.id,
        "title": document.title,
        "institution": document.institution,
        "publishedAt": document.published_at.isoformat(),
        "contentTag": document.content_tag,
        "isNew": document.published_at == publication_date,
        "analysisAvailable": document.summary_kind != "UNAVAILABLE",
        "shortSummary": (
            document.why_it_matters if document.summary_kind != "UNAVAILABLE" else None
        ),
        "keyTags": document.key_tags,
        "file": {
            "format": document.format,
            "sizeBytes": document.size_bytes,
            "pageCount": document.page_count,
            "deliveryMode": document.delivery_mode.value,
            "downloadUrl": str(document.download_url) if document.download_url else None,
            "sourceUrl": str(document.source_url),
        },
    }


def build_snapshot(
    documents: list[PublicationDocument], publication_date: date, range_key: str
) -> dict[str, Any]:
    approved = [
        item
        for item in documents
        if item.workflow_status is WorkflowStatus.APPROVED
        and item.delivery_mode is not DeliveryMode.BLOCKED
    ]
    ranked = rank_documents(approved, publication_date)
    reports: dict[str, list[dict[str, Any]]] = {}
    for topic in TOPIC_LABELS:
        if topic == "all":
            continue
        candidates = [item for item in ranked if item.primary_topic == topic]
        reports[topic] = [
            _report(item, publication_date)
            for item in _limited(candidates, 8)
        ]
    visible_ids = {
        str(report["id"])
        for topic, topic_reports in reports.items()
        if topic != "all"
        for report in topic_reports
    }
    reports["all"] = [
        _report(item, publication_date)
        for item in ranked
        if item.id in visible_ids
    ]
    topics = [
        {"id": topic, "label": label, "count": len(reports[topic])}
        for topic, label in TOPIC_LABELS.items()
    ]
    digests = {topic: {"available": False, "url": None} for topic in TOPIC_LABELS}
    return {
        "version": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "range": range_key,
        "topics": topics,
        "reportsByTopic": reports,
        "digests": digests,
    }
