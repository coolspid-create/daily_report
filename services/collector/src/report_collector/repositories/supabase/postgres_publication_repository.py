import json

import psycopg


class PostgresPublicationRepository:
    def __init__(self, database_url: str, publication_id: str) -> None:
        self.database_url = database_url
        self.publication_id = publication_id

    def stage(self, range_key: str, snapshot: dict[str, object], checksum: str) -> str:
        query = """
        insert into public.feed_snapshots(publication_id,range_key,snapshot_json,checksum)
        values(%s,%s,%s::jsonb,%s) returning id
        """
        with psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    self.publication_id,
                    range_key,
                    json.dumps(snapshot, ensure_ascii=False),
                    checksum,
                ),
            )
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("snapshot insert returned no id")
            self._replace_publication_items(cursor, snapshot)
            return str(row[0])

    def _replace_publication_items(self, cursor: psycopg.Cursor[object], snapshot: dict[str, object]) -> None:
        cursor.execute("delete from public.publication_items where publication_id=%s", (self.publication_id,))
        reports = snapshot.get("reportsByTopic", {})
        rows = self._publication_rows(reports)
        for document_id, rank, featured in rows:
            cursor.execute(
                """insert into public.publication_items(publication_id,document_id,topic_id,rank,is_featured)
                select %s,%s,primary_topic_id,%s,%s from public.documents where id=%s::uuid
                on conflict(publication_id,document_id,topic_id) do update
                  set rank=excluded.rank,is_featured=excluded.is_featured""",
                (self.publication_id, document_id, rank, featured, document_id),
            )

    def _publication_rows(self, reports: object) -> list[tuple[str, int, bool]]:
        if not isinstance(reports, dict):
            return []
        rows: dict[str, tuple[int, bool]] = {}
        for topic, items in reports.items():
            if not isinstance(items, list):
                continue
            for rank, report in enumerate(items, start=1):
                if not isinstance(report, dict) or not isinstance(report.get("id"), str):
                    continue
                document_id = report["id"]
                previous = rows.get(document_id)
                is_featured = topic == "all" or (previous[1] if previous else False)
                rows[document_id] = (previous[0] if previous else rank, is_featured)
        return [(document_id, rank, featured) for document_id, (rank, featured) in rows.items()]

    def activate(self, snapshot_id: str) -> None:
        with psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute("select public.activate_snapshot(%s)", (snapshot_id,))
