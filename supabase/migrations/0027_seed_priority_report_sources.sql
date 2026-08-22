-- Report-first expansion. Press-release collectors remain configured but inactive.
update public.sources
set active = false,
    status = 'DEGRADED',
    updated_at = now()
where slug in ('mof-press', 'fsc-policy');

insert into public.sources(
  slug,name,source_kind,list_url,homepage_url,adapter_key,config_path,rights_default,
  poll_interval_minutes,request_delay_ms,active,status
) values
  ('kistep-research','한국과학기술기획평가원 연구보고서','STATIC_BOARD','https://www.kistep.re.kr/reportAllList.es?mid=a10305010000','https://www.kistep.re.kr','kistep','config/sources/kistep-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kistep-brief','한국과학기술기획평가원 KISTEP 브리프','STATIC_BOARD','https://www.kistep.re.kr/board.es?mid=a10306010000&bid=0031','https://www.kistep.re.kr','kistep','config/sources/kistep-brief.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kisdi-policy','정보통신정책연구원 정책연구','STATIC_BOARD','https://www.kisdi.re.kr/report/list.do?arrMasterId=3934580&key=m2101113024770','https://www.kisdi.re.kr','kisdi','config/sources/kisdi-policy.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kisdi-stat','정보통신정책연구원 KISDI STAT','STATIC_BOARD','https://www.kisdi.re.kr/report/list.do?key=m2101113025790&arrMasterId=4333447','https://www.kisdi.re.kr','kisdi','config/sources/kisdi-stat.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('nabo-analysis','국회예산정책처 분석보고서','STATIC_BOARD','https://www.nabo.go.kr/ko/report/analysisList.do?key=2509250001','https://www.nabo.go.kr','nabo','config/sources/nabo-analysis.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('nabo-brief','국회예산정책처 재정경제통계 브리프','STATIC_BOARD','https://www.nabo.go.kr/ko/periodical/briefList.do?key=2507040016','https://www.nabo.go.kr','nabo','config/sources/nabo-brief.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('koti-research','한국교통연구원 기본연구보고서','STATIC_BOARD','https://www.koti.re.kr/user/bbs/bassRsrchReprtList.do','https://www.koti.re.kr','koti','config/sources/koti-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('koti-brief','한국교통연구원 KOTI 브리프','STATIC_BOARD','https://www.koti.re.kr/user/bbs/briefList.do','https://www.koti.re.kr','koti','config/sources/koti-brief.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kif-financial-brief','한국금융연구원 금융브리프','RENDERED_BOARD','https://www.kif.re.kr/kif4/publication/pub_list?mid=20','https://www.kif.re.kr','kif','config/sources/kif-financial-brief.yaml','LINK_ONLY',720,1500,true,'HEALTHY'),
  ('kif-research','한국금융연구원 연구보고서','RENDERED_BOARD','https://www.kif.re.kr/kif4/publication/pub_list?mid=10','https://www.kif.re.kr','kif','config/sources/kif-research.yaml','LINK_ONLY',720,1500,true,'HEALTHY')
on conflict (slug) do update set
  name=excluded.name, source_kind=excluded.source_kind, list_url=excluded.list_url,
  homepage_url=excluded.homepage_url, adapter_key=excluded.adapter_key,
  config_path=excluded.config_path, rights_default=excluded.rights_default,
  poll_interval_minutes=excluded.poll_interval_minutes,
  request_delay_ms=excluded.request_delay_ms, active=true, status='HEALTHY',
  consecutive_failures=0, updated_at=now();
