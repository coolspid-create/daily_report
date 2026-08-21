create or replace function public.merge_documents(
  source_document uuid,
  target_document uuid,
  actor uuid,
  merge_reason text
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if coalesce(auth.role(), '') <> 'service_role' and not public.is_admin() then
    raise exception 'admin required';
  end if;
  if source_document = target_document then
    raise exception 'source and target must differ';
  end if;
  if not exists(select 1 from public.documents where id = target_document) then
    raise exception 'target document not found';
  end if;

  update public.source_items set document_id = target_document
    where document_id = source_document;
  update public.document_sources set document_id = target_document
    where document_id = source_document;
  update public.document_files set document_id = target_document
    where document_id = source_document;
  update public.documents set workflow_status = 'REJECTED', updated_at = now()
    where id = source_document;
  insert into public.review_actions(document_id, actor_id, action, after_data, reason)
    values (
      source_document,
      actor,
      'MERGE',
      jsonb_build_object('targetDocumentId', target_document),
      merge_reason
    );
end;
$$;

revoke all on function public.merge_documents(uuid, uuid, uuid, text) from public, anon;
grant execute on function public.merge_documents(uuid, uuid, uuid, text)
  to authenticated, service_role;
