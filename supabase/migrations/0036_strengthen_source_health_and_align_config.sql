-- A successful HTTP run that discovers nothing is not proof that a collector works.
alter table public.sources
  add column if not exists consecutive_empty_runs integer not null default 0
  check (consecutive_empty_runs >= 0);

update public.sources s
set status = 'DEGRADED',
    consecutive_empty_runs = greatest(consecutive_empty_runs, 1),
    last_error_code = 'NO_CONTENT_DISCOVERED',
    last_error_message = 'Collector has completed successfully but has no stored source items',
    updated_at = now()
where s.active = true
  and s.last_success_at is not null
  and not exists (
    select 1 from public.source_items si where si.source_id = s.id
  );

-- These adapters are intentionally disabled in their checked-in configuration.
update public.sources
set active = false,
    status = 'DISABLED',
    updated_at = now()
where slug in ('kdi-research', 'korea-ratings-research', 'kis-rating-research');
