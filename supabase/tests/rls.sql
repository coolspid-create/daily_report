begin;

do $$
declare
  enabled_count integer;
begin
  select count(*) into enabled_count
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname in (
      'documents', 'review_actions', 'source_runs', 'feed_snapshots',
      'automation_runs', 'telegram_deliveries'
    )
    and c.relrowsecurity;
  if enabled_count <> 6 then
    raise exception 'expected RLS on protected tables';
  end if;
end $$;

set local role anon;
select snapshot_json from public.feed_snapshots where is_current;

do $$
begin
  begin
    perform * from public.documents limit 1;
    raise exception 'anon unexpectedly read documents';
  exception when insufficient_privilege then
    null;
  end;
end $$;

do $$
begin
  begin
    perform * from public.automation_runs limit 1;
    raise exception 'anon unexpectedly read automation runs';
  exception when insufficient_privilege then
    null;
  end;
  begin
    perform * from public.telegram_deliveries limit 1;
    raise exception 'anon unexpectedly read telegram deliveries';
  exception when insufficient_privilege then
    null;
  end;
end $$;

reset role;
set local role authenticated;
select set_config(
  'request.jwt.claims',
  '{"sub":"00000000-0000-0000-0000-000000000001","app_metadata":{"role":"admin"}}',
  true
);

do $$
begin
  perform * from public.documents limit 1;
  perform * from public.review_actions limit 1;
  perform * from public.automation_runs limit 1;
  perform * from public.telegram_deliveries limit 1;
  if not public.is_admin() then
    raise exception 'admin claim was not recognized';
  end if;
end $$;

rollback;
