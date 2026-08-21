alter table public.document_analysis
  add column if not exists summary_kind text not null default 'UNAVAILABLE'
  check (summary_kind in ('ANALYZED', 'OFFICIAL_ABSTRACT', 'UNAVAILABLE'));
