insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values (
  'krihs-research','국토연구원','STATIC_BOARD',
  'https://www.krihs.re.kr/krihsLibraryReport/reportList.es?mid=a10102000000',
  'https://www.krihs.re.kr','krihs','config/sources/krihs-research.yaml','LINK_ONLY',
  720,1500,false,'DISABLED'
) on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms;
