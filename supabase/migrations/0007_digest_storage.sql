insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('digests', 'digests', true, 52428800, array['application/pdf'])
on conflict(id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy digests_public_read on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'digests');

create policy digests_service_write on storage.objects
  for all to service_role
  using (bucket_id = 'digests')
  with check (bucket_id = 'digests');
