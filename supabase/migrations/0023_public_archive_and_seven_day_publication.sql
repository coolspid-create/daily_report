-- The public feed now publishes a rolling seven-day intake once per day.
-- Publication items are retained so a document is not sent in a later daily issue again.

alter table public.daily_publications
  drop constraint daily_publications_range_key_check;

alter table public.daily_publications
  add constraint daily_publications_range_key_check
  check (range_key in ('today', '1d', '7d'));

alter table public.feed_snapshots
  drop constraint feed_snapshots_range_key_check;

alter table public.feed_snapshots
  add constraint feed_snapshots_range_key_check
  check (range_key in ('today', '1d', '7d'));

-- Backfill the delivery ledger from the featured reports in previously published snapshots.
-- Old snapshots may contain the same report more than once after a rebuild; the unique key
-- deliberately keeps one ledger row per publication/document/topic.
insert into public.publication_items(publication_id,document_id,topic_id,rank,is_featured)
select
  snapshot.publication_id,
  (report.value ->> 'id')::uuid,
  document.primary_topic_id,
  report.ordinality::integer,
  true
from public.feed_snapshots snapshot
join public.daily_publications publication on publication.id=snapshot.publication_id
cross join lateral jsonb_array_elements(snapshot.snapshot_json #> '{reportsByTopic,all}')
  with ordinality as report(value, ordinality)
join public.documents document on document.id=(report.value ->> 'id')::uuid
where publication.status='PUBLISHED'
on conflict(publication_id,document_id,topic_id) do nothing;

-- Archive reads are deliberately exposed only through these narrow RPCs. This keeps internal
-- document and review data inaccessible while allowing the public one-page archive selector.
create or replace function public.public_archive_dates(maximum integer default 14)
returns table(publication_date date)
language sql
stable
security definer
set search_path = ''
as $$
  select distinct publication.publication_date
  from public.feed_snapshots snapshot
  join public.daily_publications publication on publication.id=snapshot.publication_id
  where publication.status='PUBLISHED' and snapshot.range_key='7d'
  order by publication.publication_date desc
  limit greatest(1, least(coalesce(maximum, 14), 31));
$$;

create or replace function public.public_archive_snapshot(target_date date)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select snapshot.snapshot_json
  from public.feed_snapshots snapshot
  join public.daily_publications publication on publication.id=snapshot.publication_id
  where publication.status='PUBLISHED'
    and publication.publication_date=target_date
    and snapshot.range_key='7d'
  order by snapshot.created_at desc
  limit 1;
$$;

revoke all on function public.public_archive_dates(integer) from public;
revoke all on function public.public_archive_snapshot(date) from public;
grant execute on function public.public_archive_dates(integer) to anon, authenticated;
grant execute on function public.public_archive_snapshot(date) to anon, authenticated;
