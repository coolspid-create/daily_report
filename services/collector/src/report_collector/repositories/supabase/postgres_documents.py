from datetime import date, timedelta

import psycopg
from psycopg.rows import dict_row
from report_collector.domain.enums import DeliveryMode, WorkflowStatus
from report_collector.domain.models import PublicationDocument
from report_collector.services.publication_eligibility import EXCLUDED_PUBLIC_SOURCE_SLUGS


def load_approved_documents(
    database_url: str, publication_date: date, range_key: str
) -> list[PublicationDocument]:
    days = {"today": 0, "1d": 1, "7d": 7}.get(range_key)
    if days is None:
        raise ValueError(f"Unsupported publication range: {range_key}")
    earliest = publication_date - timedelta(days=days)
    query = """
    select d.id,d.canonical_title,d.institution,d.published_at,d.primary_topic_id,d.content_tag,
      d.why_it_matters,d.delivery_mode,d.primary_source_url,a.summary_kind,a.key_points,a.key_tags,
      f.file_url,f.extension,f.size_bytes,f.page_count,
      coalesce((
        select source.content_type
        from public.document_sources document_source
        join public.sources source on source.id=document_source.source_id
        where document_source.document_id=d.id
        order by source.created_at asc
        limit 1
      ), 'REPORT') as source_content_type
    from public.documents d
    join public.document_analysis a on a.document_id=d.id
    left join lateral (
      select * from public.document_files where document_id=d.id and validation_status='VALID'
      order by created_at desc limit 1
    ) f on true
    where d.workflow_status='APPROVED' and d.published_at between %s and %s
      and not exists (
        select 1
        from public.document_sources excluded_document_source
        join public.sources excluded_source
          on excluded_source.id=excluded_document_source.source_id
        where excluded_document_source.document_id=d.id
          and excluded_source.slug = any(%s)
      )
      and not exists (
        select 1
        from public.publication_items previous_item
        join public.daily_publications previous_publication
          on previous_publication.id=previous_item.publication_id
        where previous_item.document_id=d.id
          and previous_publication.status='PUBLISHED'
          and previous_publication.range_key=%s
          and previous_publication.publication_date < %s
      )
    """
    with (
        psycopg.connect(database_url, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            query,
            (
                earliest,
                publication_date,
                list(EXCLUDED_PUBLIC_SOURCE_SLUGS),
                range_key,
                publication_date,
            ),
        )
        rows = cursor.fetchall()
    return [
        PublicationDocument(
            id=str(row["id"]),
            title=row["canonical_title"],
            institution=row["institution"],
            published_at=row["published_at"],
            primary_topic=row["primary_topic_id"],
            content_tag=row["content_tag"],
            why_it_matters=row["why_it_matters"],
            summary_kind=row["summary_kind"],
            key_points=row["key_points"],
            key_tags=row["key_tags"],
            delivery_mode=DeliveryMode(row["delivery_mode"]),
            source_url=row["primary_source_url"],
            download_url=row["file_url"],
            format=row["extension"].upper() if row["extension"] else None,
            size_bytes=row["size_bytes"],
            page_count=row["page_count"],
            workflow_status=WorkflowStatus.APPROVED,
            source_content_type=row["source_content_type"],
            ranking_score=0.8,
        )
        for row in rows
    ]


def ensure_publication(database_url: str, publication_date: date, range_key: str) -> str:
    query = """
    insert into public.daily_publications(publication_date,range_key,status)
    values(%s,%s,'BUILDING') on conflict(publication_date,range_key)
    do update set status='BUILDING' returning id
    """
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query, (publication_date, range_key))
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("publication upsert returned no id")
        return str(row[0])


def load_current_snapshot(database_url: str, range_key: str) -> dict[str, object]:
    query = "select snapshot_json from public.feed_snapshots where range_key=%s and is_current order by created_at desc limit 1"
    with (
        psycopg.connect(database_url, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(query, (range_key,))
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("current snapshot not found")
        return row["snapshot_json"]  # type: ignore[no-any-return]
