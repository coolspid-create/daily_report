insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('kiet-research','산업연구원','RENDERED_BOARD','https://www.kiet.re.kr/research/reportList','https://www.kiet.re.kr',
   'rendered_board','config/sources/kiet-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('keei-research','에너지경제연구원','RENDERED_BOARD','https://www.keei.re.kr/board.es?mid=a10101010000&bid=0001','https://www.keei.re.kr',
   'rendered_board','config/sources/keei-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('kinu-research','통일연구원','STATIC_BOARD','https://www.kinu.or.kr/main/module/report/index.do?nav_code=mai1674786094','https://www.kinu.or.kr',
   'static_board','config/sources/kinu-research.yaml','LINK_ONLY',720,1500,false,'DISABLED')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms;
