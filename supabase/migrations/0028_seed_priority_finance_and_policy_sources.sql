-- Public report expansion: only sources with stable, ordinary public HTML links are active.
insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('kita-report','한국무역협회 통상리포트','STATIC_BOARD','https://www.kita.net/researchTrade/report/reportMain/reportMainList.do','https://www.kita.net','kita','config/sources/kita-report.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kcif-public-reports','국제금융센터 공개 리포트','STATIC_BOARD','https://www.kcif.or.kr/annual/monthlyList','https://www.kcif.or.kr','kcif','config/sources/kcif-public-reports.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('nafi-research','국회미래연구원 연구보고서','STATIC_BOARD','https://nafi.re.kr/home/kor/board.do?menuPos=13','https://nafi.re.kr','nafi','config/sources/nafi-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kcmi-research','자본시장연구원 연구보고서','STATIC_BOARD','https://www.kcmi.re.kr/report/report_list','https://www.kcmi.re.kr','kcmi','config/sources/kcmi-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kdb-future-strategy','KDB미래전략연구소','RENDERED_BOARD','https://rd.kdb.co.kr/FLSRIA02N01.act','https://rd.kdb.co.kr/FLMNMN00N01.act','kdb','config/sources/kdb-future-strategy.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('ibk-economy-research','IBK경제연구소 경제분석','STATIC_BOARD','https://research.ibk.co.kr/research/board/economy/list','https://research.ibk.co.kr','static_board','config/sources/ibk-economy-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kis-rating-research','한국신용평가 공개 리서치','STATIC_BOARD','https://www.kisrating.com','https://www.kisrating.com','static_board','config/sources/kis-rating-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('nice-credit-research','NICE신용평가 공개 리서치','STATIC_BOARD','https://www.nicerating.com/research/issueReport.do','https://www.nicerating.com','static_board','config/sources/nice-credit-research.yaml','LINK_ONLY',720,1500,false,'DISABLED'),
  ('korea-ratings-research','한국기업평가 공개 리서치','STATIC_BOARD','https://www.korearatings.com/ratingsInfo/researchList.do','https://www.korearatings.com','static_board','config/sources/korea-ratings-research.yaml','LINK_ONLY',720,1500,false,'DISABLED')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, active=excluded.active,
  status=excluded.status, consecutive_failures=0, updated_at=now();
