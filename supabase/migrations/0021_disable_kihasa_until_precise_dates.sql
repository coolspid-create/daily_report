-- The current KIHASA list exposes only a publication year, so it cannot meet
-- the one-day publication window without risking stale reports.
update public.sources
set active = false,
    status = 'DEGRADED',
    updated_at = now()
where slug = 'kihasa-research';
