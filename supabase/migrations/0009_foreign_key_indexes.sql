create index document_files_document_idx
  on public.document_files(document_id);
create index document_files_source_item_idx
  on public.document_files(source_item_id)
  where source_item_id is not null;
create index document_sources_source_idx
  on public.document_sources(source_id);
create index document_sources_source_item_idx
  on public.document_sources(source_item_id);
create index documents_primary_topic_idx
  on public.documents(primary_topic_id)
  where primary_topic_id is not null;
create index feed_snapshots_publication_idx
  on public.feed_snapshots(publication_id);
create index publication_items_document_idx
  on public.publication_items(document_id);
create index publication_items_topic_idx
  on public.publication_items(topic_id);
create index review_actions_actor_idx
  on public.review_actions(actor_id);
create index review_actions_document_idx
  on public.review_actions(document_id);
create index source_items_document_idx
  on public.source_items(document_id)
  where document_id is not null;
