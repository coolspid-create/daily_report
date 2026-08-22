from __future__ import annotations

import json
from pathlib import PurePosixPath

import psycopg
from report_collector.domain.models import SourceDocument
from report_collector.services.deduplication_service import normalize_title
from report_collector.services.rights_service import choose_delivery, is_session_dependent_url


def load_active_source_slugs(database_url: str) -> set[str]:
    query = "select slug from public.sources where active=true"
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query)
        return {str(row[0]) for row in cursor.fetchall()}


class PostgresSourceRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def get_cursor(self, source_id: str) -> str | None:
        query = "select cursor_after from public.source_runs where source_id=(select id from public.sources where slug=%s) and status='SUCCEEDED' order by finished_at desc limit 1"
        with psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(query, (source_id,))
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] else None

    def _document_id(self, cursor: psycopg.Cursor, document: SourceDocument) -> str:
        normalized = normalize_title(document.title)
        cursor.execute(
            "select id from public.documents where primary_source_url=%s or (normalized_title=%s and institution=%s and published_at is not distinct from %s) order by created_at limit 1",
            (str(document.detail_url), normalized, document.institution, document.published_at),
        )
        existing = cursor.fetchone()
        if existing:
            return str(existing[0])
        attachment = document.attachments[0] if document.attachments else None
        delivery = choose_delivery(
            document.rights_status,
            official_file_stable=bool(attachment),
            session_dependent=bool(
                attachment and is_session_dependent_url(str(attachment.url))
            ),
            mirrored_file_exists=False,
            source_available=True,
        )
        cursor.execute(
            "insert into public.documents(canonical_title,normalized_title,institution,published_at,rights_status,delivery_mode,primary_source_url) values(%s,%s,%s,%s,%s,%s,%s) returning id",
            (
                document.title,
                normalized,
                document.institution,
                document.published_at,
                document.rights_status.value,
                delivery.value,
                str(document.detail_url),
            ),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("document insert returned no id")
        return str(row[0])

    def _source_item_id(
        self, cursor: psycopg.Cursor, source_id: str, document: SourceDocument, document_id: str
    ) -> str:
        query = """
        insert into public.source_items(
          source_id,source_item_key,list_title,list_published_at,detail_url,document_id,raw_metadata
        ) select id,%s,%s,%s,%s,%s,%s::jsonb from public.sources where slug=%s
        on conflict(source_id,source_item_key) do update set
          list_title=excluded.list_title,last_seen_at=now(),document_id=excluded.document_id,
          raw_metadata=excluded.raw_metadata returning id
        """
        cursor.execute(
            query,
            (
                document.source_item_key,
                document.title,
                document.published_at,
                str(document.detail_url),
                document_id,
                json.dumps(document.model_dump(mode="json")),
                source_id,
            ),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"source not seeded: {source_id}")
        return str(row[0])

    def _link_source(
        self, cursor: psycopg.Cursor, source_id: str, source_item_id: str, document_id: str
    ) -> None:
        cursor.execute(
            "insert into public.document_sources(document_id,source_id,source_item_id,detail_url,is_original_publisher) select %s,id,%s,(select detail_url from public.source_items where id=%s),true from public.sources where slug=%s on conflict(document_id,source_item_id) do nothing",
            (document_id, source_item_id, source_item_id, source_id),
        )

    def _link_files(
        self, cursor: psycopg.Cursor, document: SourceDocument, source_item_id: str, document_id: str
    ) -> None:
        for attachment in document.attachments:
            extension = PurePosixPath(attachment.file_name).suffix.lstrip(".")
            cursor.execute(
                "insert into public.document_files(document_id,source_item_id,file_url,file_name,mime_type,extension) select %s,%s,%s,%s,%s,%s where not exists(select 1 from public.document_files where document_id=%s and file_url=%s)",
                (
                    document_id,
                    source_item_id,
                    str(attachment.url),
                    attachment.file_name,
                    attachment.declared_type,
                    extension or None,
                    document_id,
                    str(attachment.url),
                ),
            )
            cursor.execute(
                "update public.document_files set file_name=%s,mime_type=%s,extension=%s where document_id=%s and file_url=%s",
                (
                    attachment.file_name,
                    attachment.declared_type,
                    extension or None,
                    document_id,
                    str(attachment.url),
                ),
            )

    def _refresh_delivery(
        self, cursor: psycopg.Cursor, document: SourceDocument, document_id: str
    ) -> None:
        attachment = document.attachments[0] if document.attachments else None
        if attachment is None:
            return
        delivery = choose_delivery(
            document.rights_status,
            official_file_stable=True,
            session_dependent=is_session_dependent_url(str(attachment.url)),
            mirrored_file_exists=False,
            source_available=True,
        )
        cursor.execute(
            "update public.documents set delivery_mode=%s,updated_at=now() where id=%s and delivery_mode<>'BLOCKED'",
            (delivery.value, document_id),
        )

    def save_document(self, source_id: str, document: SourceDocument) -> str | None:
        with psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            document_id = self._document_id(cursor, document)
            item_id = self._source_item_id(cursor, source_id, document, document_id)
            self._link_source(cursor, source_id, item_id, document_id)
            self._link_files(cursor, document, item_id, document_id)
            self._refresh_delivery(cursor, document, document_id)
        return document_id

    def finish_run(self, source_id: str, cursor: str | None, discovered: int, failed: int) -> None:
        run_query = """
        insert into public.source_runs(source_id,finished_at,status,discovered_count,new_count,failed_count,cursor_after)
        select id,now(),%s,%s,%s,%s,%s from public.sources where slug=%s
        """
        status = "SUCCEEDED" if failed == 0 else "PARTIAL"
        source_query = """
        update public.sources
        set status = case when %s = 0 then 'HEALTHY' else 'DEGRADED' end,
            last_success_at = case when %s = 0 then now() else last_success_at end,
            consecutive_failures = case when %s = 0 then 0 else consecutive_failures + 1 end,
            updated_at = now()
        where slug = %s
        """
        with psycopg.connect(self.database_url) as connection, connection.cursor() as db_cursor:
            db_cursor.execute(
                run_query, (status, discovered, discovered - failed, failed, cursor, source_id)
            )
            db_cursor.execute(source_query, (failed, failed, failed, source_id))

    def fail_run(self, source_id: str, error_code: str, error_message: str) -> None:
        run_query = """
        insert into public.source_runs(source_id,finished_at,status,failed_count,error_code,error_message)
        select id,now(),'FAILED',1,%s,%s from public.sources where slug=%s
        """
        source_query = """
        update public.sources
        set status='DEGRADED', consecutive_failures=consecutive_failures+1, updated_at=now()
        where slug=%s
        """
        with psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(run_query, (error_code, error_message[:1_000], source_id))
            cursor.execute(source_query, (source_id,))
