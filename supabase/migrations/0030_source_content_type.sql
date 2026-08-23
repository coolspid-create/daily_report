alter table public.sources
  add column if not exists content_type text not null default 'REPORT';

alter table public.sources
  drop constraint if exists sources_content_type_check;

alter table public.sources
  add constraint sources_content_type_check
  check (content_type in ('REPORT', 'PRESS_RELEASE'));

-- 보도자료 파이프라인은 유지하되, 공개 리포트 발행본과 분리한다.
update public.sources
set content_type = 'PRESS_RELEASE', updated_at = now()
where slug in ('mof-press', 'fsc-policy');
