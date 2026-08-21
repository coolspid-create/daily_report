insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  (
    'kotra-market-news','KOTRA 해외시장뉴스','STATIC_BOARD',
    'https://dream.kotra.or.kr/kotranews/index.do',
    'https://dream.kotra.or.kr/kotranews/index.do',
    'kotra','config/sources/kotra-market-news.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
  ),
  (
    'keis-research','한국고용정보원','STATIC_BOARD',
    'https://www.keis.or.kr/keis/ko/proj/113/pblc/list.do','https://www.keis.or.kr',
    'keis','config/sources/keis-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
  ),
  (
    'kmi-research','한국해양수산개발원','STATIC_BOARD',
    'https://www.kmi.re.kr/web/board/list.do?rbsIdx=384','https://www.kmi.re.kr',
    'kmi','config/sources/kmi-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
  ),
  (
    'fsc-policy','금융위원회','STATIC_BOARD',
    'https://www.fsc.go.kr/no000000','https://www.fsc.go.kr',
    'fsc','config/sources/fsc-policy.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
  ),
  (
    'kb-research','KB경영연구소','STATIC_BOARD',
    'https://www.kbfg.com/kbresearch/report/reportList.do',
    'https://www.kbfg.com/kbresearch/report/reportList.do',
    'kb','config/sources/kb-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'
  )
on conflict (slug) do update set
  name=excluded.name,
  source_kind=excluded.source_kind,
  list_url=excluded.list_url,
  homepage_url=excluded.homepage_url,
  adapter_key=excluded.adapter_key,
  config_path=excluded.config_path,
  rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms,
  active=true,
  status='HEALTHY',
  consecutive_failures=0,
  updated_at=now();
