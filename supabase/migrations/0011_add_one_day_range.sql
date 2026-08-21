-- Existing seven-day publications remain readable for audit and rollback.
-- New production writes and the public app use only today and 1d.
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
