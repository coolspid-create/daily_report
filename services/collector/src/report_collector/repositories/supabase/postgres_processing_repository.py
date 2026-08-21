import json
from pathlib import Path

import psycopg
from report_collector.domain.models import AnalysisResult
from report_collector.services.file_validation_service import ValidatedPdf


def save_processing_result(
    database_url: str,
    document_id: str,
    analysis: AnalysisResult,
    file_url: str | None,
    validation: ValidatedPdf | None,
    temporary_path: Path | None,
    ttl_hours: int,
) -> None:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        if file_url and validation and temporary_path:
            cursor.execute(
                "update public.document_files set size_bytes=%s,page_count=%s,sha256=%s,is_encrypted=false,validation_status='VALID',storage_path=%s,expires_at=now()+(%s * interval '1 hour') where document_id=%s and file_url=%s",
                (
                    validation.size_bytes,
                    validation.page_count,
                    validation.sha256,
                    str(temporary_path),
                    ttl_hours,
                    document_id,
                    file_url,
                ),
            )
        cursor.execute(
            "update public.documents set why_it_matters=%s,content_tag=%s,primary_topic_id=%s,summary_status='COMPLETED',workflow_status=case when workflow_status='APPROVED' then 'APPROVED' else 'NEEDS_REVIEW' end,updated_at=now() where id=%s",
            (
                analysis.why_it_matters,
                analysis.content_tag,
                analysis.topic_candidates[0],
                document_id,
            ),
        )
        cursor.execute(
            "insert into public.document_analysis(document_id,why_it_matters,summary_kind,key_points,key_tags,secondary_topic_ids,content_tag,confidence,evidence_pages,analysis_version,prompt_version,provider_key,extractor_version,full_text_retained_until) values(%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb,'1','1','extractive-pdf','pymupdf-1',now()+(%s * interval '1 hour')) on conflict(document_id) do update set why_it_matters=excluded.why_it_matters,summary_kind=excluded.summary_kind,key_points=excluded.key_points,key_tags=excluded.key_tags,secondary_topic_ids=excluded.secondary_topic_ids,content_tag=excluded.content_tag,confidence=excluded.confidence,evidence_pages=excluded.evidence_pages,provider_key=excluded.provider_key,updated_at=now(),full_text_retained_until=excluded.full_text_retained_until",
            (
                document_id,
                analysis.why_it_matters,
                analysis.summary_kind,
                json.dumps(analysis.key_points, ensure_ascii=False),
                json.dumps(analysis.key_tags, ensure_ascii=False),
                json.dumps(analysis.topic_candidates[1:]),
                analysis.content_tag,
                analysis.confidence,
                json.dumps(analysis.evidence_pages),
                ttl_hours,
            ),
        )
        cursor.execute("delete from public.document_topics where document_id=%s", (document_id,))
        for index, topic_id in enumerate(analysis.topic_candidates):
            cursor.execute(
                "insert into public.document_topics(document_id,topic_id,score,is_primary) values(%s,%s,%s,%s)",
                (document_id, topic_id, max(analysis.confidence - index * 0.1, 0), index == 0),
            )


def mark_file_invalid(database_url: str, document_id: str, file_url: str) -> None:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "update public.document_files set validation_status='INVALID',expires_at=now() where document_id=%s and file_url=%s",
            (document_id, file_url),
        )
        cursor.execute(
            "update public.documents set delivery_mode='OFFICIAL_PAGE_ONLY',updated_at=now() where id=%s",
            (document_id,),
        )


def clear_expired_processing_data(database_url: str) -> tuple[int, int]:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "update public.document_files set storage_path=null where expires_at<=now() and storage_path is not null"
        )
        cleared_files = cursor.rowcount
        cursor.execute(
            "update public.document_analysis set full_text_retained_until=null where full_text_retained_until<=now()"
        )
        cleared_text_markers = cursor.rowcount
    return cleared_files, cleared_text_markers
