import json
from datetime import date
from pathlib import Path

import pytest
from report_collector.domain.enums import DeliveryMode, WorkflowStatus
from report_collector.domain.models import PublicationDocument
from report_collector.pipelines.publish_snapshot import publish_snapshot
from report_collector.repositories.publication_repository import MemoryPublicationRepository
from report_collector.services.publication_service import build_snapshot


def document(
    identifier: str, status: WorkflowStatus = WorkflowStatus.APPROVED
) -> PublicationDocument:
    return PublicationDocument(
        id=identifier,
        title=f"보고서 {identifier}",
        institution="공공연구원",
        published_at=date(2026, 8, 21),
        primary_topic="ai-tech",
        content_tag="정책 변화",
        why_it_matters="중요한 정책 변화입니다.",
        key_points=["핵심 1", "핵심 2", "핵심 3"],
        key_tags=["정책", "변화", "검토"],
        delivery_mode=DeliveryMode.OFFICIAL_PAGE_ONLY,
        source_url=f"https://official.example/{identifier}",
        workflow_status=status,
        ranking_score=0.9,
    )


def test_only_approved_documents_are_published(contract_root: Path) -> None:
    snapshot = build_snapshot(
        [document("approved"), document("rejected", WorkflowStatus.REJECTED)],
        date(2026, 8, 21),
        "today",
    )
    ids = [report["id"] for report in snapshot["reportsByTopic"]["all"]]
    assert ids == ["approved"]
    schema = json.loads((contract_root / "public-feed.schema.json").read_text(encoding="utf-8"))
    repository = MemoryPublicationRepository()
    publish_snapshot(snapshot, schema, repository, lambda _: None)
    assert repository.current_payload("today") == snapshot


def test_all_topic_contains_the_sum_of_topic_documents() -> None:
    first = document("ai")
    second = document("economy").model_copy(update={"primary_topic": "economy"})

    snapshot = build_snapshot([first, second], date(2026, 8, 21), "today")

    assert snapshot["topics"][0]["count"] == 2
    assert len(snapshot["reportsByTopic"]["all"]) == 2
    assert len(snapshot["reportsByTopic"]["ai-tech"]) == 1
    assert len(snapshot["reportsByTopic"]["economy"]) == 1


def test_failed_snapshot_build_keeps_previous(contract_root: Path) -> None:
    schema = json.loads((contract_root / "public-feed.schema.json").read_text(encoding="utf-8"))
    repository = MemoryPublicationRepository()
    previous = build_snapshot([document("previous")], date(2026, 8, 20), "today")
    publish_snapshot(previous, schema, repository, lambda _: None)
    current_before = repository.current_payload("today")

    def fail(_: dict[str, object]) -> None:
        raise RuntimeError("digest failed")

    with pytest.raises(RuntimeError, match="digest failed"):
        publish_snapshot(
            build_snapshot([document("new")], date(2026, 8, 21), "today"), schema, repository, fail
        )
    assert repository.current_payload("today") == current_before
