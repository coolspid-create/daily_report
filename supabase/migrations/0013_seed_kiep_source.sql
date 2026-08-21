insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values (
  'kiep-research','대외경제정책연구원','STATIC_BOARD',
  'https://www.kiep.go.kr/gallery.es?bid=0001&mid=a10101020000&nPage=1&tag=',
  'https://www.kiep.go.kr','static_board','config/sources/kiep-research.yaml','LINK_ONLY',
  720,1500,false,'DISABLED'
) on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms;
