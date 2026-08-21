insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values (
  'inss-issue-brief','국가안보전략연구원','STATIC_BOARD',
  'https://www.inss.re.kr/publication/bbs/ib_list.do','https://www.inss.re.kr',
  'inss','config/sources/inss-issue-brief.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
)
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, active=true, status='HEALTHY',
  consecutive_failures=0, updated_at=now();
