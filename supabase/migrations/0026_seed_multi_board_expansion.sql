insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('hana-research','하나금융연구소 연구보고서','STATIC_BOARD','https://www.hanaif.re.kr/boardList.do?menuId=MN1000&tabMenuId=N','https://www.hanaif.re.kr/main.do','hana','config/sources/hana-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('hana-focus','하나금융연구소 하나금융포커스','STATIC_BOARD','https://www.hanaif.re.kr/boardList.do?menuId=MN2100&tabMenuId=MN2102','https://www.hanaif.re.kr/main.do','hana','config/sources/hana-focus.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('hana-wealth','하나금융연구소 대한민국 웰스 리포트','STATIC_BOARD','https://www.hanaif.re.kr/boardList.do?menuId=MN2000&tabMenuId=MN2500','https://www.hanaif.re.kr/main.do','hana','config/sources/hana-wealth.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('keis-employment-issue','한국고용정보원 고용이슈','STATIC_BOARD','https://www.keis.or.kr/keis/ko/proj/117/pblc/list.do?categoryIdx=130','https://www.keis.or.kr/keis/ko/index.do','keis','config/sources/keis-employment-issue.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('keis-employment-trend','한국고용정보원 고용동향브리프','STATIC_BOARD','https://www.keis.or.kr/keis/ko/proj/118/pblc/list.do?categoryIdx=126','https://www.keis.or.kr/keis/ko/index.do','keis','config/sources/keis-employment-trend.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('mof-press','해양수산부 보도자료','STATIC_BOARD','https://www.mof.go.kr/doc/ko/selectDocList.do?menuSeq=971&bbsSeq=10','https://www.mof.go.kr/index.do?menuSeq=971','mof','config/sources/mof-press.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('mof-policy','해양수산부 정책게시판','STATIC_BOARD','https://www.mof.go.kr/doc/ko/selectDocList.do?menuSeq=1009&bbsSeq=22','https://www.mof.go.kr/index.do?menuSeq=1008','mof','config/sources/mof-policy.yaml','LINK_ONLY',720,1500,true,'HEALTHY')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key, config_path=excluded.config_path,
  rights_default=excluded.rights_default, poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, active=true, status='HEALTHY',
  consecutive_failures=0, updated_at=now();
