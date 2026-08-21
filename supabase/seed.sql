insert into public.topics (id, label, sort_order) values
  ('economy', '경제·금융', 1),
  ('industry', '산업·통상', 2),
  ('ai-tech', 'AI·과학기술', 3),
  ('labor-welfare', '노동·복지', 4),
  ('education-population', '교육·인구', 5),
  ('land-environment', '국토·환경', 6),
  ('law-security', '법·외교·안보', 7)
on conflict (id) do update set label = excluded.label, sort_order = excluded.sort_order;

insert into public.sources
  (slug, name, source_kind, list_url, homepage_url, adapter_key, config_path, rights_default)
values
  ('nars', '국회입법조사처', 'STATIC_BOARD', 'https://www.nars.go.kr/report/list.do', 'https://www.nars.go.kr', 'static_board', 'config/sources/nars.yaml', 'LINK_ONLY'),
  ('kdi-research', '한국개발연구원', 'RENDERED_BOARD', 'https://www.kdi.re.kr/research/reportList', 'https://www.kdi.re.kr', 'rendered_board', 'config/sources/kdi-research.yaml', 'LINK_ONLY'),
  ('bok-rss', '한국은행', 'RSS', 'https://www.bok.or.kr/portal/bbs/P0002353/news.rss?menuNo=200433', 'https://www.bok.or.kr', 'rss', 'config/sources/bok-rss.yaml', 'LINK_ONLY'),
  ('kihasa-research', '한국보건사회연구원', 'RENDERED_BOARD', 'https://www.kihasa.re.kr/publish/report/list?type=research', 'https://www.kihasa.re.kr', 'rendered_board', 'config/sources/kihasa-research.yaml', 'LINK_ONLY')
on conflict (slug) do update set name = excluded.name, config_path = excluded.config_path;
