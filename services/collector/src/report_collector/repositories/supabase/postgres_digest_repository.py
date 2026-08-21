import psycopg


def save_digest(
    database_url: str,
    publication_id: str,
    topic_id: str,
    storage_path: str,
    size_bytes: int,
    checksum: str,
) -> None:
    query = """
    insert into public.digest_files(
      publication_id,topic_id,storage_path,file_size_bytes,checksum,status
    ) values(%s,%s,%s,%s,%s,'READY')
    on conflict(publication_id,topic_id) do update set
      storage_path=excluded.storage_path,
      file_size_bytes=excluded.file_size_bytes,
      checksum=excluded.checksum,
      generated_at=now(),
      status='READY'
    """
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            (publication_id, topic_id, storage_path, size_bytes, checksum),
        )


def set_publication_status(database_url: str, publication_id: str, status: str) -> None:
    query = """
    update public.daily_publications
    set status=%s, published_at=case when %s='PUBLISHED' then now() else null end
    where id=%s
    """
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query, (status, status, publication_id))
