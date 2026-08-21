create table public.review_actions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  actor_id uuid not null references auth.users(id),
  action text not null check (action in ('UPDATE', 'APPROVE', 'HOLD', 'REJECT', 'MERGE')),
  before_data jsonb not null default '{}'::jsonb,
  after_data jsonb not null default '{}'::jsonb,
  reason text,
  created_at timestamptz not null default now()
);

create table public.daily_publications (
  id uuid primary key default gen_random_uuid(),
  publication_date date not null,
  range_key text not null check (range_key in ('today', '7d')),
  status text not null default 'BUILDING' check (status in ('BUILDING', 'PUBLISHED', 'FAILED')),
  published_at timestamptz,
  snapshot_version integer not null default 1,
  unique(publication_date, range_key)
);

create table public.publication_items (
  id uuid primary key default gen_random_uuid(),
  publication_id uuid not null references public.daily_publications(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  topic_id text not null references public.topics(id),
  rank integer not null check (rank > 0),
  is_featured boolean not null default false,
  unique(publication_id, document_id, topic_id)
);

create index publication_items_publication_topic_rank_idx
  on public.publication_items(publication_id, topic_id, rank);

create table public.feed_snapshots (
  id uuid primary key default gen_random_uuid(),
  publication_id uuid not null references public.daily_publications(id) on delete cascade,
  range_key text not null check (range_key in ('today', '7d')),
  snapshot_json jsonb not null,
  checksum text not null check (checksum ~ '^[a-f0-9]{64}$'),
  created_at timestamptz not null default now(),
  is_current boolean not null default false
);

create unique index feed_snapshots_one_current_idx
  on public.feed_snapshots(range_key) where is_current;
create index feed_snapshots_current_range_idx on public.feed_snapshots(is_current, range_key);

create table public.digest_files (
  id uuid primary key default gen_random_uuid(),
  publication_id uuid not null references public.daily_publications(id) on delete cascade,
  topic_id text not null,
  storage_path text not null,
  file_size_bytes bigint not null check (file_size_bytes > 0),
  checksum text not null check (checksum ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null default now(),
  status text not null check (status in ('READY', 'FAILED')),
  unique(publication_id, topic_id)
);
