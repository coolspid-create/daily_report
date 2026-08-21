-- Sources with a known parser or collection failure remain configured, but are
-- excluded from scheduled collection and the administrator's active source list.
update public.sources
set active = false,
    status = 'DEGRADED',
    updated_at = now()
where slug in ('kdi-research', 'kli-research', 'stepi-research');
