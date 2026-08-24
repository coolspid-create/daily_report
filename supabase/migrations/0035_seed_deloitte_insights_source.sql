-- Seed Deloitte Korea Insights as an active public report research source
insert into public.sources (
  slug, name, source_kind, list_url, homepage_url, adapter_key, config_path,
  rights_default, content_type, poll_interval_minutes, request_delay_ms, active, status
) values (
  'deloitte-insights',
  '딜로이트 인사이트',
  'STATIC_BOARD',
  'https://www.deloitte.com/kr/ko/our-thinking/deloitte-insights-publications.html',
  'https://www.deloitte.com/kr/ko/our-thinking/deloitte-insights.html',
  'static_board',
  'config/sources/deloitte-insights.yaml',
  'LINK_ONLY',
  'REPORT',
  720,
  1500,
  true,
  'HEALTHY'
)
on conflict (slug) do update set
  name = excluded.name,
  source_kind = excluded.source_kind,
  list_url = excluded.list_url,
  homepage_url = excluded.homepage_url,
  adapter_key = excluded.adapter_key,
  config_path = excluded.config_path,
  content_type = excluded.content_type,
  active = true,
  status = 'HEALTHY',
  updated_at = now();
