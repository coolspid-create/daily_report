import json
from dataclasses import dataclass
from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class PendingTelegramDelivery:
    publication_id: str
    publication_date: date
    snapshot: dict[str, Any]
    destination_key: str


def load_pending_telegram_deliveries(
    database_url: str, limit: int = 5
) -> list[PendingTelegramDelivery]:
    query = """
    select t.publication_id,p.publication_date,f.snapshot_json,t.destination_key
    from public.telegram_deliveries t join public.daily_publications p on p.id=t.publication_id
    join lateral (select snapshot_json from public.feed_snapshots
      where publication_id=p.id order by created_at desc limit 1) f on true
    where t.status='PENDING' and t.attempt_count < 3 order by t.updated_at limit %s
    """
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        rows = connection.execute(query, (limit,)).fetchall()
    return [
        PendingTelegramDelivery(
            str(row["publication_id"]),
            row["publication_date"],
            dict(row["snapshot_json"]),
            str(row["destination_key"]),
        )
        for row in rows
    ]


def begin_telegram_delivery(
    database_url: str, publication_id: str, destination_key: str
) -> str | None:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        row = connection.execute(
            """insert into public.telegram_deliveries(publication_id,destination_key)
            values(%s,%s) on conflict(publication_id,destination_key) do update
            set updated_at=now() returning id,status""",
            (publication_id, destination_key),
        ).fetchone()
        if not row or str(row["status"]) == "SENT":
            return None
        connection.execute(
            """update public.telegram_deliveries set status='SENDING',attempt_count=attempt_count+1,
            last_error=null,updated_at=now() where id=%s""",
            (row["id"],),
        )
        return str(row["id"])


def complete_telegram_delivery(
    database_url: str, delivery_id: str, message_ids: list[str]
) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """update public.telegram_deliveries set status='SENT',message_ids=%s::jsonb,
            sent_at=now(),updated_at=now() where id=%s""",
            (json.dumps(message_ids), delivery_id),
        )


def fail_telegram_delivery(database_url: str, delivery_id: str, error: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """update public.telegram_deliveries set status='FAILED',last_error=%s,
            updated_at=now() where id=%s""",
            (error[:1000], delivery_id),
        )
