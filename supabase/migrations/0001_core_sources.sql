create extension if not exists pgcrypto;

create table public.sources (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  source_kind text not null check (source_kind in ('STATIC_BOARD', 'RENDERED_BOARD', 'RSS')),
  list_url text not null check (list_url ~ '^https://'),
  homepage_url text not null check (homepage_url ~ '^https://'),
  adapter_key text not null,
  config_path text not null,
  rights_default text not null default 'LINK_ONLY'
    check (rights_default in ('FILE_UPLOAD_ALLOWED', 'LINK_ONLY', 'MANUAL_REVIEW', 'BLOCKED')),
  poll_interval_minutes integer not null default 720 check (poll_interval_minutes >= 60),
  request_delay_ms integer not null default 1200 check (request_delay_ms >= 500),
  active boolean not null default true,
  status text not null default 'HEALTHY' check (status in ('HEALTHY', 'DEGRADED', 'DISABLED')),
  last_success_at timestamptz,
  consecutive_failures integer not null default 0 check (consecutive_failures >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.source_runs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references public.sources(id) on delete cascade,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'RUNNING' check (status in ('RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED')),
  discovered_count integer not null default 0,
  new_count integer not null default 0,
  updated_count integer not null default 0,
  failed_count integer not null default 0,
  cursor_before text,
  cursor_after text,
  error_code text,
  error_message text
);

create index source_runs_source_started_idx on public.source_runs(source_id, started_at desc);

create table public.source_items (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references public.sources(id) on delete cascade,
  source_item_key text not null,
  list_title text not null,
  list_published_at timestamptz,
  detail_url text not null,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  document_id uuid,
  raw_metadata jsonb not null default '{}'::jsonb,
  unique(source_id, source_item_key)
);

create index source_items_source_key_idx on public.source_items(source_id, source_item_key);
