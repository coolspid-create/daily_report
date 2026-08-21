update public.sources
set active = true, status = 'HEALTHY', consecutive_failures = 0, updated_at = now()
where slug in (
  'nars', 'krihs-research', 'kiep-research', 'kei-research', 'kiet-research',
  'kedi-research', 'keei-research', 'kinu-research', 'kipf-research'
);

update public.sources
set active = false, status = 'DEGRADED', updated_at = now()
where slug = 'stepi-research';

update public.sources
set active = false, status = 'DEGRADED', updated_at = now()
where slug = 'kli-research';
