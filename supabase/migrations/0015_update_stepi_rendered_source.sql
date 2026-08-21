update public.sources
set source_kind='RENDERED_BOARD', adapter_key='stepi', updated_at=now()
where slug='stepi-research';
