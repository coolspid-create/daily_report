insert into public.sources (
  slug, name, source_kind, homepage_url, list_url, adapter_key, config_path,
  rights_default, content_type, poll_interval_minutes, request_delay_ms, active, status
) values
  ('korea-policy-documents','대한민국 정부 정책브리핑 전문자료','STATIC_BOARD','https://www.korea.kr','https://www.korea.kr/archive/expDocMainList.do','static_board','config/sources/korea-policy-documents.yaml','LINK_ONLY','REPORT',720,1200,true,'HEALTHY'),
  ('samil-pwc-insights','삼일PwC 인사이트','RENDERED_BOARD','https://www.pwc.com/kr/ko/insights.html','https://www.pwc.com/kr/ko/insights/issue-brief.html','rendered_board','config/sources/samil-pwc-insights.yaml','LINK_ONLY','REPORT',720,1200,true,'HEALTHY'),
  ('ibks-research','IBK투자증권 리서치','RENDERED_BOARD','https://www.ibks.com','https://m.ibks.com/iko/IKO010101.do','rendered_board','config/sources/ibks-research.yaml','LINK_ONLY','REPORT',720,1500,true,'HEALTHY'),
  ('kiwoom-research','키움증권 리서치','STATIC_BOARD','https://www.kiwoom.com','https://t.me/s/KiwoomResearch','static_board','config/sources/kiwoom-research.yaml','LINK_ONLY','REPORT',720,1200,true,'HEALTHY'),
  ('sk-securities-research','SK증권 리서치','STATIC_BOARD','https://www.sks.co.kr','https://t.me/s/sksresearch','static_board','config/sources/sk-securities-research.yaml','LINK_ONLY','REPORT',720,1200,true,'HEALTHY')
on conflict (slug) do update set
  name=excluded.name,
  source_kind=excluded.source_kind,
  homepage_url=excluded.homepage_url,
  list_url=excluded.list_url,
  adapter_key=excluded.adapter_key,
  config_path=excluded.config_path,
  rights_default=excluded.rights_default,
  content_type=excluded.content_type,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms,
  active=true,
  status='HEALTHY',
  consecutive_failures=0,
  consecutive_empty_runs=0,
  updated_at=now();
