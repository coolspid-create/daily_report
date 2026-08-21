insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('kedi-research','한국교육개발원','RENDERED_BOARD','https://www.kedi.re.kr/khome/main/research/listPubForm.do?plNum0=7037','https://www.kedi.re.kr',
   'kedi','config/sources/kedi-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('kipf-research','한국조세재정연구원','RENDERED_BOARD','https://www.kipf.re.kr/kor/Publication/KipfReport/kiPublish/CA/list.do','https://www.kipf.re.kr',
   'kipf','config/sources/kipf-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('kli-research','한국노동연구원','STATIC_BOARD','https://www.kli.re.kr/kli/prePrdclView.es?mid=a10102060000','https://www.kli.re.kr',
   'kli','config/sources/kli-research.yaml','LINK_ONLY',720,1500,false,'DEGRADED')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, status=excluded.status;
