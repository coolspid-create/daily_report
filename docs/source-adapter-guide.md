# 출처 어댑터 가이드

## 허용 경계

새 출처는 공개 HTML, 공식 RSS/Atom, 공개 첨부파일 링크, 정상적인 브라우저 렌더링 중 하나만 사용합니다. 공식·비공식 API, Open API, 숨은 JSON/XHR URL 직접 호출, 로그인·유료·CAPTCHA 우회는 금지합니다. 브라우저가 페이지를 정상 렌더링하며 자체적으로 불러오는 자원은 허용하지만 그 엔드포인트를 Collector가 직접 호출하도록 바꾸면 안 됩니다.

## 추가 순서

1. 기관 공식 홈페이지에서 목록·상세·첨부 URL과 이용 조건을 확인합니다.
2. `config/sources/<slug>.yaml`에 `static_board`, `rendered_board`, `rss` 중 하나를 선언합니다.
3. 범용 selector로 충분하면 generic adapter를 사용합니다. JS 함수형 링크처럼 고유 규칙이 있으면 `adapters/sources/<slug>/adapter.py`를 만듭니다.
4. 목록과 상세 HTML/RSS를 `services/collector/tests/fixtures`에 저장하고 네트워크 없는 회귀 테스트를 추가합니다.
5. `python scripts/check-source-configs.py`와 `python scripts/check-collector-policy.py`를 실행합니다.
6. 실제 사이트 검증은 `@pytest.mark.live`로 작성해 `source-smoke.yml`에서만 실행합니다.

모든 출처는 독립 YAML과 fixture를 가져야 합니다. adapter는 발견·상세 해석에만 집중하고 중복 제거, 권리, 분석, 발행 규칙을 포함하지 않습니다. 요청 간격은 최소 500ms이고 현재 실제 출처는 1500ms입니다.

## 초기 3개 출처

- 국회입법조사처: 정적 HTML 게시판과 공개 첨부 링크
- 한국개발연구원: Playwright를 통한 공개 페이지 렌더링
- 한국은행: 공식 RSS 목록, 상세는 공식 페이지 우선

KDI가 제공하는 별도 Open API는 사용하지 않습니다. 세 출처 모두 `LINK_ONLY`로 시작하며 fixture가 기본 CI, live 호출은 주간 또는 수동 smoke입니다.

## 전국 확장 게이트

후보 출처는 `docs/nationwide-source-expansion.md`에만 먼저 등록합니다. 후보 등록은 수집 활성화가 아닙니다. 각 기관은 아래 기준을 모두 통과한 뒤에만 `config/sources/`로 옮깁니다.

1. 공식 목록 URL, 상세 URL, 공식 파일 링크와 저작권 안내를 사람이 확인합니다.
2. 공개 HTML, 공식 RSS/Atom 또는 정상 브라우저 렌더링만으로 목록과 상세를 읽을 수 있어야 합니다.
3. 최근 1일 자료가 실제로 목록에서 식별되고, 과거 자료를 대량 백필하지 않아야 합니다.
4. 기관 전용 YAML, 목록·상세 fixture, parser 회귀 테스트와 별도 live smoke를 만듭니다.
5. 직접 파일 URL은 MIME·서명·크기 검증을 통과한 경우에만 노출하며 기본 권리 상태는 `LINK_ONLY`입니다.
6. 최소 3회 smoke가 연속 성공하고, 운영자가 검수 화면에서 결과와 링크를 확인한 뒤 활성화합니다.
