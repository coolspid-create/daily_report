create table public.documents (
  id uuid primary key default gen_random_uuid(),
  canonical_title text not null,
  normalized_title text not null,
  institution text not null,
  published_at date,
  summary_status text not null default 'PENDING'
    check (summary_status in ('PENDING', 'COMPLETED', 'SUMMARY_FAILED')),
  workflow_status text not null default 'NEW'
    check (workflow_status in ('NEW', 'NEEDS_REVIEW', 'APPROVED', 'REJECTED', 'PUBLISHED')),
  primary_topic_id text,
  content_tag text,
  why_it_matters text,
  rights_status text not null default 'LINK_ONLY'
    check (rights_status in ('FILE_UPLOAD_ALLOWED', 'LINK_ONLY', 'MANUAL_REVIEW', 'BLOCKED')),
  delivery_mode text not null default 'OFFICIAL_PAGE_ONLY'
    check (delivery_mode in ('DIRECT_OFFICIAL_FILE', 'OFFICIAL_PAGE_ONLY', 'MIRRORED_ALLOWED', 'SUMMARY_ONLY', 'BLOCKED')),
  primary_source_url text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.source_items
  add constraint source_items_document_fk foreign key (document_id) references public.documents(id);

create index documents_title_date_idx on public.documents(normalized_title, published_at);
create index documents_workflow_date_idx on public.documents(workflow_status, published_at desc);

create table public.document_sources (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  source_id uuid not null references public.sources(id) on delete cascade,
  source_item_id uuid not null references public.source_items(id) on delete cascade,
  detail_url text not null,
  is_original_publisher boolean not null default false,
  priority integer not null default 100,
  unique(document_id, source_item_id)
);

create table public.document_files (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  source_item_id uuid references public.source_items(id) on delete set null,
  file_url text not null,
  file_name text not null,
  mime_type text,
  extension text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  page_count integer check (page_count is null or page_count > 0),
  sha256 text check (sha256 is null or sha256 ~ '^[a-f0-9]{64}$'),
  is_encrypted boolean not null default false,
  validation_status text not null default 'PENDING'
    check (validation_status in ('PENDING', 'VALID', 'INVALID', 'TOO_LARGE', 'ENCRYPTED')),
  storage_path text,
  expires_at timestamptz,
  created_at timestamptz not null default now()
);

create index document_files_sha256_idx on public.document_files(sha256) where sha256 is not null;
