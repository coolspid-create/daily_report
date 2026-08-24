-- Seed ministry press release sources to ensure all 60 active sources exist in database
insert into public.sources (
  slug, name, source_kind, list_url, homepage_url, adapter_key, config_path,
  rights_default, content_type, poll_interval_minutes, request_delay_ms, active, status
) values
  ('ftc-press', '공정거래위원회 보도자료', 'STATIC_BOARD', 'https://www.ftc.go.kr/www/selectReportUserList.do?key=10', 'https://www.ftc.go.kr', 'static_board', 'config/sources/ftc-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('moef-press', '기획재정부 보도자료', 'STATIC_BOARD', 'https://www.moef.go.kr/nw/nes/nesdta.do?bbsId=MOSFBBS_000000000028&menuNo=4010100', 'https://www.moef.go.kr', 'static_board', 'config/sources/moef-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('moel-press', '고용노동부 보도자료', 'STATIC_BOARD', 'https://www.moel.go.kr/news/enews/report/enewsList.do', 'https://www.moel.go.kr', 'static_board', 'config/sources/moel-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('mohw-press', '보건복지부 보도자료', 'STATIC_BOARD', 'https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027', 'https://www.mohw.go.kr', 'static_board', 'config/sources/mohw-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('molit-press', '국토교통부 보도자료', 'STATIC_BOARD', 'https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp', 'https://www.molit.go.kr', 'static_board', 'config/sources/molit-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('motie-press', '산업통상자원부 보도자료', 'STATIC_BOARD', 'https://www.motie.go.kr/kor/article/ATCL3f49a5a8c', 'https://www.motie.go.kr', 'static_board', 'config/sources/motie-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('msit-press', '과학기술정보통신부 보도자료', 'STATIC_BOARD', 'https://www.msit.go.kr/bbs/list.do?sCode=user&mPid=112&mId=113&bbsSeqNo=42', 'https://www.msit.go.kr', 'static_board', 'config/sources/msit-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY'),
  ('mss-press', '중소벤처기업부 보도자료', 'STATIC_BOARD', 'https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=86', 'https://www.mss.go.kr', 'static_board', 'config/sources/mss-press.yaml', 'LINK_ONLY', 'PRESS_RELEASE', 720, 1500, true, 'HEALTHY')
on conflict (slug) do update set
  name = excluded.name,
  source_kind = excluded.source_kind,
  list_url = excluded.list_url,
  homepage_url = excluded.homepage_url,
  adapter_key = excluded.adapter_key,
  config_path = excluded.config_path,
  content_type = excluded.content_type,
  active = true,
  status = 'HEALTHY',
  updated_at = now();
