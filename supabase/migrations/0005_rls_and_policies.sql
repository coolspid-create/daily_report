create or replace function public.is_admin()
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select coalesce((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false)
$$;

alter table public.sources enable row level security;
alter table public.source_runs enable row level security;
alter table public.source_items enable row level security;
alter table public.documents enable row level security;
alter table public.document_sources enable row level security;
alter table public.document_files enable row level security;
alter table public.document_analysis enable row level security;
alter table public.topics enable row level security;
alter table public.document_topics enable row level security;
alter table public.review_actions enable row level security;
alter table public.daily_publications enable row level security;
alter table public.publication_items enable row level security;
alter table public.feed_snapshots enable row level security;
alter table public.digest_files enable row level security;

create policy topics_public_read on public.topics for select to anon, authenticated using (active);
create policy current_snapshots_public_read on public.feed_snapshots
  for select to anon, authenticated using (is_current);
create policy ready_digests_public_read on public.digest_files
  for select to anon, authenticated using (
    status = 'READY'
    and exists (
      select 1 from public.feed_snapshots snapshot
      where snapshot.publication_id = digest_files.publication_id
        and snapshot.is_current
    )
  );

create policy admin_sources_all on public.sources for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_source_runs_all on public.source_runs for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_source_items_all on public.source_items for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_documents_all on public.documents for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_document_sources_all on public.document_sources for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_document_files_all on public.document_files for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_document_analysis_all on public.document_analysis for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_document_topics_all on public.document_topics for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_review_actions_all on public.review_actions for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_publications_all on public.daily_publications for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_publication_items_all on public.publication_items for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_snapshots_all on public.feed_snapshots for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy admin_digests_all on public.digest_files for all to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));

revoke all on all tables in schema public from anon, authenticated;
grant select on public.topics, public.feed_snapshots, public.digest_files to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;

create or replace function public.activate_snapshot(target_snapshot uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  target_range text;
begin
  if coalesce(auth.role(), '') <> 'service_role'
    and session_user not like 'postgres%'
    and not public.is_admin() then
    raise exception 'admin required';
  end if;
  select range_key into strict target_range
    from public.feed_snapshots where id = target_snapshot;
  update public.feed_snapshots set is_current = false
    where range_key = target_range and is_current;
  update public.feed_snapshots set is_current = true where id = target_snapshot;
end;
$$;

revoke all on function public.activate_snapshot(uuid) from public, anon;
grant execute on function public.activate_snapshot(uuid) to authenticated, service_role;
