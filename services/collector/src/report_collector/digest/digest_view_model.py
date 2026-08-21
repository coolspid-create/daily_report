from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DigestViewModel:
    date_label: str
    topic_label: str
    generated_at: str
    reports: list[dict[str, Any]]


def build_digest_view_model(snapshot: dict[str, Any], topic_id: str) -> DigestViewModel:
    labels = {topic["id"]: topic["label"] for topic in snapshot["topics"]}
    reports = snapshot["reportsByTopic"].get(topic_id, [])
    generated = str(snapshot["generatedAt"])
    return DigestViewModel(
        date_label=generated[:10],
        topic_label=labels.get(topic_id, topic_id),
        generated_at=generated,
        reports=reports,
    )
