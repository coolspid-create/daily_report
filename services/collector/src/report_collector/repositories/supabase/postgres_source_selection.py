import psycopg


def load_active_source_slugs(database_url: str) -> set[str]:
    """Return enabled sources, excluding those awaiting a scheduled recovery probe."""
    query = "select slug from public.sources where active=true and status <> 'DISABLED'"
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query)
        return {str(row[0]) for row in cursor.fetchall()}


def load_all_active_source_slugs_by_content_type(
    database_url: str, content_type: str
) -> set[str]:
    """Return active sources including automatically disabled ones for a fallback run."""
    query = "select slug from public.sources where active=true and content_type=%s"
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query, (content_type,))
        return {str(row[0]) for row in cursor.fetchall()}


def load_retryable_press_source_slugs(
    database_url: str, source_ids: tuple[str, ...]
) -> set[str]:
    """Return only currently active, degraded press sources from an initial failed batch."""
    if not source_ids:
        return set()
    query = """
        select slug from public.sources
        where slug = any(%s)
          and active = true
          and status = 'DEGRADED'
          and content_type = 'PRESS_RELEASE'
    """
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query, (list(source_ids),))
        return {str(row[0]) for row in cursor.fetchall()}


def load_recovery_probe_press_source_slugs(database_url: str) -> set[str]:
    return load_recovery_probe_source_slugs(database_url, "PRESS_RELEASE")


def load_recovery_probe_source_slugs(database_url: str, content_type: str) -> set[str]:
    """Probe automatically disabled sources at most once per Korean calendar day."""
    query = """
        select slug from public.sources
        where active = true
          and status = 'DISABLED'
          and content_type = %s
          and consecutive_failures >= 5
          and (last_failure_at is null or
            (last_failure_at at time zone 'Asia/Seoul')::date <
            (now() at time zone 'Asia/Seoul')::date)
    """
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query, (content_type,))
        return {str(row[0]) for row in cursor.fetchall()}
