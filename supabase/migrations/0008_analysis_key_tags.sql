alter table public.document_analysis
  add column key_tags jsonb not null default '["검수 필요"]'::jsonb
  check (jsonb_typeof(key_tags) = 'array' and jsonb_array_length(key_tags) between 1 and 3);
