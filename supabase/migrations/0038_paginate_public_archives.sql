-- Date-only metadata can be paged independently of document/snapshot payloads.
create or replace function public.public_archive_dates_page(
  page_offset integer default 0, page_size integer default 100
)
returns table(publication_date date)
language sql stable security definer set search_path = ''
as $$
  select distinct p.publication_date
  from public.daily_publications p
  join public.feed_snapshots s on s.publication_id = p.id
  where p.status = 'PUBLISHED' and s.range_key = '7d'
    and coalesce(jsonb_array_length(s.snapshot_json #> '{reportsByTopic,all}'), 0) > 0
  order by p.publication_date desc
  limit greatest(1, least(coalesce(page_size, 100), 100))
  offset greatest(0, coalesce(page_offset, 0));
$$;
revoke all on function public.public_archive_dates_page(integer, integer) from public;
grant execute on function public.public_archive_dates_page(integer, integer) to anon, authenticated, service_role;

-- Match the same explicit source classification used by selected-date queries.
create or replace function public.press_archive_dates_page(
  page_offset integer default 0, page_size integer default 100
)
returns table(publication_date date)
language sql stable security invoker set search_path = ''
as $$
  select distinct coalesce(d.published_at, (d.created_at at time zone 'UTC')::date) as publication_date
  from public.documents d
  where d.workflow_status in ('APPROVED', 'PUBLISHED')
    and exists (
      select 1 from public.document_sources ds
      join public.sources s on s.id = ds.source_id
      where ds.document_id = d.id and s.content_type = 'PRESS_RELEASE'
    )
  order by publication_date desc
  limit greatest(1, least(coalesce(page_size, 100), 100))
  offset greatest(0, coalesce(page_offset, 0));
$$;
revoke all on function public.press_archive_dates_page(integer, integer) from public, anon, authenticated;
grant execute on function public.press_archive_dates_page(integer, integer) to service_role;
