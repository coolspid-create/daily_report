from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row


class AutomationAlreadyCompleted(RuntimeError):
    pass


class AutomationAlreadyRunning(RuntimeError):
    pass


@dataclass(frozen=True)
class AutomationRunResult:
    run_id: str
    resumed: bool


def start_automation_run(
    database_url: str,
    scheduled_for: datetime,
    window_start: datetime,
    window_end: datetime,
) -> AutomationRunResult:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        connection.execute(
            """update public.automation_runs set status='FAILED',stage='FINISHED',
            error_code='STALE_RUN',
            error_message='A previous automation run stopped without completing.',
            finished_at=now(),updated_at=now()
            where status='RUNNING' and updated_at < now() - interval '2 hours'"""
        )
        row = connection.execute(
            """insert into public.automation_runs(scheduled_for,window_started_at,window_ended_at,status)
            values(%s,%s,%s,'RUNNING') on conflict(scheduled_for) do nothing returning id""",
            (scheduled_for, window_start, window_end),
        ).fetchone()
        if row:
            return AutomationRunResult(str(row["id"]), False)
        existing = connection.execute(
            "select id,status from public.automation_runs where scheduled_for=%s",
            (scheduled_for,),
        ).fetchone()
        if not existing or str(existing["status"]) in {"PUBLISHED", "NO_CONTENT", "DRY_RUN"}:
            raise AutomationAlreadyCompleted("the scheduled automation already completed")
        if str(existing["status"]) == "RUNNING":
            raise AutomationAlreadyRunning("the scheduled automation is already running")
        connection.execute(
            """update public.automation_runs set status='RUNNING',stage='STARTED',
            error_message=null,finished_at=null,updated_at=now() where id=%s""",
            (existing["id"],),
        )
        return AutomationRunResult(str(existing["id"]), True)


def update_automation_stage(database_url: str, run_id: str, stage: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "update public.automation_runs set stage=%s,updated_at=now() where id=%s",
            (stage, run_id),
        )


def record_collection_finished(
    database_url: str, run_id: str, finished_at: datetime, collected_count: int = 0
) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """update public.automation_runs set collection_finished_at=%s,
            window_ended_at=%s,collected_count=%s,updated_at=now() where id=%s""",
            (finished_at, finished_at, max(0, collected_count), run_id),
        )


def finish_automation_run(
    database_url: str,
    run_id: str,
    status: str,
    counts: dict[str, int],
    error_message: str | None = None,
    window_ended_at: datetime | None = None,
) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """update public.automation_runs set status=%s,stage='FINISHED',
            collected_count=%s,review_candidate_count=%s,approved_count=%s,exception_count=%s,
            published_count=%s,delivered_count=%s,error_message=%s,
            window_ended_at=coalesce(%s, window_ended_at),
            collection_finished_at=coalesce(%s, collection_finished_at),
            finished_at=now(),updated_at=now() where id=%s""",
            (
                status,
                counts.get("collected", 0),
                counts.get("review_candidates", counts.get("collected", 0)),
                counts.get("approved", 0),
                counts.get("exceptions", 0),
                counts.get("published", 0),
                counts.get("telegram", 0),
                error_message,
                window_ended_at,
                window_ended_at,
                run_id,
            ),
        )
