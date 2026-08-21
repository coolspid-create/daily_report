create table public.topics (
  id text primary key,
  label text not null,
  sort_order integer not null unique,
  active boolean not null default true
);

alter table public.documents
  add constraint documents_primary_topic_fk foreign key (primary_topic_id) references public.topics(id);

create table public.document_analysis (
  document_id uuid primary key references public.documents(id) on delete cascade,
  why_it_matters text not null,
  key_points jsonb not null check (jsonb_typeof(key_points) = 'array'),
  secondary_topic_ids jsonb not null default '[]'::jsonb,
  content_tag text not null,
  confidence numeric not null check (confidence between 0 and 1),
  evidence_pages jsonb not null default '[]'::jsonb,
  analysis_version text not null,
  prompt_version text not null,
  provider_key text not null,
  extractor_version text not null,
  full_text_retained_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.document_topics (
  document_id uuid not null references public.documents(id) on delete cascade,
  topic_id text not null references public.topics(id),
  score numeric not null check (score between 0 and 1),
  is_primary boolean not null default false,
  primary key(document_id, topic_id)
);

create index document_topics_topic_score_idx on public.document_topics(topic_id, score desc);
