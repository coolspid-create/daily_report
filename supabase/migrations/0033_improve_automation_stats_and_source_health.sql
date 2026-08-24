-- Improve automation stats and source health recording
-- 1. Automation runs: distinguish review candidate count from actual newly collected documents
alter table public.automation_runs
  add column if not exists review_candidate_count integer not null default 0,
  add column if not exists collection_finished_at timestamptz;

-- 2. Sources: record timeout, retries, failure timestamps and error messages
alter table public.sources
  add column if not exists last_failure_at timestamptz,
  add column if not exists last_error_code text,
  add column if not exists last_error_message text,
  add column if not exists timeout_seconds integer not null default 30,
  add column if not exists max_retries integer not null default 2;

-- 3. Source runs: prevent negative counts
update public.source_runs set new_count = 0 where new_count < 0;
update public.source_runs set discovered_count = 0 where discovered_count < 0;
update public.source_runs set updated_count = 0 where updated_count < 0;
update public.source_runs set failed_count = 0 where failed_count < 0;

alter table public.source_runs
  drop constraint if exists source_runs_non_negative_counts;

alter table public.source_runs
  add constraint source_runs_non_negative_counts
  check (discovered_count >= 0 and new_count >= 0 and updated_count >= 0 and failed_count >= 0);
