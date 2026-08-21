from datetime import datetime
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from report_collector.domain.enums import DeliveryMode, RightsStatus
from report_collector.services.auto_approval_policy import (
    AutoApprovalCandidate,
    AutoApprovalDecision,
)


def load_auto_review_candidates(
    database_url: str, window_start: datetime, window_end: datetime
) -> list[AutoApprovalCandidate]:
    query = """
    select d.id,d.published_at,coalesce(seen.first_seen_at,d.created_at) first_seen_at,
      exists(select 1 from public.document_sources ds join public.sources s on s.id=ds.source_id
        where ds.document_id=d.id and s.active) source_active,
      exists(select 1 from public.document_sources ds join public.sources s on s.id=ds.source_id
        where ds.document_id=d.id and s.active and s.status='HEALTHY') source_healthy,
      d.rights_status,d.delivery_mode,d.summary_status,d.why_it_matters,d.primary_source_url,
      a.summary_kind,a.key_tags,a.confidence,coalesce(duplicates.count,0) duplicate_count,
      exists(select 1 from public.document_files f where f.document_id=d.id
        and f.file_url ~* '[?&](token|session|expires|signature)=') has_session_file_url
    from public.documents d
    left join public.document_analysis a on a.document_id=d.id
    left join lateral (
      select min(si.first_seen_at) first_seen_at from public.document_sources ds
      join public.source_items si on si.id=ds.source_item_id where ds.document_id=d.id
    ) seen on true
    left join lateral (
      select count(distinct other.id) count from public.documents other
      where other.id<>d.id and (
        other.primary_source_url=d.primary_source_url
        or (other.normalized_title=d.normalized_title and other.institution=d.institution
          and other.published_at is not distinct from d.published_at)
        or exists(select 1 from public.document_files mine join public.document_files other_file
          on other_file.sha256=mine.sha256 and other_file.document_id=other.id
          where mine.document_id=d.id and mine.sha256 is not null)
      )
    ) duplicates on true
    where d.workflow_status in ('NEW','NEEDS_REVIEW')
      and coalesce(seen.first_seen_at,d.created_at) between %s and %s
    order by d.created_at
    """
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        rows = connection.execute(query, (window_start, window_end)).fetchall()
    return [_candidate(row) for row in rows]


def _candidate(row: dict[str, object]) -> AutoApprovalCandidate:
    confidence = row["confidence"]
    duplicate_count = row["duplicate_count"]
    return AutoApprovalCandidate(
        document_id=str(row["id"]),
        published_at=row["published_at"],  # type: ignore[arg-type]
        first_seen_at=row["first_seen_at"],  # type: ignore[arg-type]
        source_active=bool(row["source_active"]),
        source_healthy=bool(row["source_healthy"]),
        rights_status=RightsStatus(str(row["rights_status"])),
        delivery_mode=DeliveryMode(str(row["delivery_mode"])),
        summary_status=str(row["summary_status"]),
        summary_kind=str(row["summary_kind"]) if row["summary_kind"] else None,
        why_it_matters=str(row["why_it_matters"]) if row["why_it_matters"] else None,
        key_tags=tuple(row["key_tags"] or ()),  # type: ignore[arg-type]
        confidence=float(confidence) if isinstance(confidence, (int, float, Decimal)) else None,
        source_url=str(row["primary_source_url"]),
        duplicate_count=int(duplicate_count) if isinstance(duplicate_count, (int, float)) else 0,
        has_session_file_url=bool(row["has_session_file_url"]),
    )


def apply_auto_review_decisions(
    database_url: str,
    decisions: list[AutoApprovalDecision],
    policy_version: str,
) -> tuple[int, int]:
    approved = 0
    held = 0
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        for decision in decisions:
            action = "AUTO_APPROVE" if decision.approved else "AUTO_HOLD"
            if decision.approved:
                cursor.execute(
                    "update public.documents set workflow_status='APPROVED',updated_at=now() where id=%s and workflow_status in ('NEW','NEEDS_REVIEW')",
                    (decision.document_id,),
                )
                approved += cursor.rowcount
            else:
                cursor.execute(
                    "update public.documents set workflow_status='NEEDS_REVIEW',updated_at=now() where id=%s and workflow_status='NEW'",
                    (decision.document_id,),
                )
                held += 1
            cursor.execute(
                "insert into public.review_actions(document_id,actor_id,actor_kind,action,after_data,policy_version) select %s,null,'SYSTEM',%s,jsonb_build_object('reasonCodes',%s::jsonb),%s where not exists(select 1 from public.review_actions where document_id=%s and action=%s and policy_version=%s)",
                (
                    decision.document_id,
                    action,
                    _reason_json(decision.reason_codes),
                    policy_version,
                    decision.document_id,
                    action,
                    policy_version,
                ),
            )
    return approved, held


def _reason_json(reason_codes: tuple[str, ...]) -> str:
    import json

    return json.dumps(list(reason_codes))
