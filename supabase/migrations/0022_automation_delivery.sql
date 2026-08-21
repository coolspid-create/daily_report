alter table public.review_actions alter column actor_id drop not null;
alter table public.review_actions
  add column actor_kind text not null default 'ADMIN'
    check (actor_kind in ('ADMIN', 'SYSTEM')),
  add column policy_version text;
alter table public.review_actions drop constraint review_actions_action_check;
alter table public.review_actions add constraint review_actions_action_check
  check (action in ('UPDATE', 'APPROVE', 'HOLD', 'REJECT', 'MERGE', 'AUTO_APPROVE', 'AUTO_HOLD'));
alter table public.review_actions add constraint review_actions_actor_check
  check (
    (actor_kind = 'ADMIN' and actor_id is not null)
    or (actor_kind = 'SYSTEM' and actor_id is null)
  );

create table public.automation_runs (
  id uuid primary key default gen_random_uuid(),
  scheduled_for timestamptz not null unique,
  window_started_at timestamptz not null,
  window_ended_at timestamptz not null,
  status text not null check (status in ('RUNNING', 'PUBLISHED', 'PARTIAL', 'FAILED', 'NO_CONTENT', 'DRY_RUN')),
  stage text not null default 'STARTING',
  collected_count integer not null default 0,
  eligible_count integer not null default 0,
  approved_count integer not null default 0,
  exception_count integer not null default 0,
  published_count integer not null default 0,
  delivered_count integer not null default 0,
  error_code text,
  error_message text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  updated_at timestamptz not null default now()
);

create table public.telegram_deliveries (
  id uuid primary key default gen_random_uuid(),
  publication_id uuid not null references public.daily_publications(id) on delete cascade,
  destination_key text not null,
  status text not null default 'PENDING'
    check (status in ('PENDING', 'SENDING', 'SENT', 'FAILED')),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  message_ids jsonb not null default '[]'::jsonb,
  last_error text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(publication_id, destination_key)
);

create index automation_runs_started_idx on public.automation_runs(started_at desc);
create index telegram_deliveries_status_idx on public.telegram_deliveries(status, updated_at);

alter table public.automation_runs enable row level security;
alter table public.telegram_deliveries enable row level security;
create policy admin_automation_runs_all on public.automation_runs for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_telegram_deliveries_all on public.telegram_deliveries for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
grant select, insert, update, delete on public.automation_runs to authenticated;
grant select, insert, update, delete on public.telegram_deliveries to authenticated;
