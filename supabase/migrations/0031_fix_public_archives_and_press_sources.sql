-- 공개 리포트 아카이브에는 실제 공개 카드가 있는 발행본만 노출한다.
create or replace function public.public_archive_dates(maximum integer default 14)
returns table(publication_date date)
language sql
stable
security definer
set search_path = ''
as $$
  select distinct publication.publication_date
  from public.daily_publications as publication
  join public.feed_snapshots as snapshot on snapshot.publication_id = publication.id
  where publication.status = 'PUBLISHED'
    and snapshot.range_key = '7d'
    and coalesce(jsonb_array_length(snapshot.snapshot_json #> '{reportsByTopic,all}'), 0) > 0
  order by publication.publication_date desc
  limit greatest(1, least(coalesce(maximum, 14), 31));
$$;

revoke all on function public.public_archive_dates(integer) from public;
grant execute on function public.public_archive_dates(integer) to anon, authenticated;

-- 보도자료 수집기는 최근 실행이 성공했지만 과거 상태가 남아 비활성화되어 있었다.
update public.sources
set active = true,
    status = 'HEALTHY',
    consecutive_failures = 0,
    updated_at = now()
where slug in ('fsc-policy', 'mof-press')
  and content_type = 'PRESS_RELEASE';
