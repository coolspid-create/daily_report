-- Added only for public research/report boards. Press-release boards remain disabled.
insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('posri-research','포스코경영연구원 연구보고서','STATIC_BOARD','https://www.posri.re.kr/kor/bbs/report_list.do?mmcd=2402221432440016120&cate=2403071010350015910','https://www.posri.re.kr/kor/index.do','static_board','config/sources/posri-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('hri-research','현대경제연구원 연구보고서','STATIC_BOARD','https://www.hri.co.kr/kor/report?mode=1','https://www.hri.co.kr/kor/main','static_board','config/sources/hri-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('wfri-research','우리금융경영연구소 연구보고서','STATIC_BOARD','https://www.wfri.re.kr/ko/web/research_report/research_report.php','https://www.wfri.re.kr/ko/web/main.php','static_board','config/sources/wfri-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('fki-report','한국경제인협회 연구자료','STATIC_BOARD','https://www.fki.or.kr/kor/publication/report.do','https://www.fki.or.kr/kor/main/main.do','static_board','config/sources/fki-report.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('keri-research','한국경제연구원 KERI 연구자료','STATIC_BOARD','https://www.keri.org/keri/publication/research.do','https://www.keri.org/keri/main.do','static_board','config/sources/keri-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('ifans-focus','외교안보연구소 IFANS FOCUS','STATIC_BOARD','https://www.ifans.go.kr/knda/ifans/kor/pblct/PblctList.do?menuCl=P07','https://www.ifans.go.kr/knda/ifans/kor/main/IfansMain.do','static_board','config/sources/ifans-focus.yaml','LINK_ONLY',720,1500,true,'HEALTHY')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, active=excluded.active,
  status=excluded.status, consecutive_failures=0, updated_at=now();
