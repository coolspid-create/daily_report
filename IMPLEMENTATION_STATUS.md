# 구현 상태

## Phase 0 — 기반

- 구현: monorepo, 환경 예시, Node/Python 품질 도구, 세 JSON Schema, 7개 migration, 7개 분야 seed, Docker Collector, 파일 크기 검사.
- 검증: 계약/source/migration 정적 검사, Ruff, mypy, pytest, ESLint, TypeScript, Vitest, Next build.
- 위험: 현재 Windows 호스트에는 Docker/Supabase CLI가 없어 실제 로컬 RLS 실행은 CI 대상으로 남아 있습니다.

## Phase 1 — Collector 핵심

- 구현: 세 adapter 유형, YAML validator, retry/timeout/delay/cursor, 가상 출처 2개와 네트워크 없는 fixture.
- 검증: 정적·렌더링·RSS parser, source filter와 외부 API 금지 자동 검사.
- 위험: 실제 웹 구조는 변할 수 있어 별도 주간 smoke가 필요합니다.

## Phase 2 — 문서 처리

- 구현: 문서/출처/첨부 DB 연결, PDF 임시 다운로드, MIME·서명·크기·암호화, SHA-256, PyMuPDF 추출, 중복 판정, 상태 머신, 48시간 cleanup.
- 검증: 정상/손상/HTML 위장 PDF, URL/hash/title 중복, 상태 전이, 수집 후 분석 저장 통합 테스트.
- 위험: OCR 엔진은 범위에서 제외되어 텍스트가 부족한 PDF는 관리자 검수로 보냅니다.

## Phase 3 — 관리자 검수

- 구현: Supabase 관리자 로그인, `/admin` 인라인 작업대, 검수/승인/제외, 해시 중복 후보의 트랜잭션 병합, 출처 상태 API.
- 검증: 입력 schema, 익명 `/admin` 로그인 전환, 관리자 claim RLS SQL.
- 위험: 실제 관리자 계정과 Supabase가 없는 로컬 fixture 모드에서는 DB 쓰기 E2E를 수행할 수 없습니다.

## Phase 4 — 공개 한 페이지 피드

- 구현: `/` 단일 공개 화면, 분야·기간·localStorage·query 동기화, 즉시 snapshot 필터, delivery mode별 버튼과 빈 상태.
- 검증: Vitest 13개와 데스크톱/모바일 Playwright E2E 4개, 브라우저 시각·hydration 검사.
- 위험: 로컬 fixture의 공식 링크는 기능 확인용 기관 홈 URL입니다.

## Phase 5 — 분석·선별·스냅샷

- 구현: provider interface와 mock, 구조화 분석, ranking, 승인 전용 snapshot, current 단일 포인터.
- 검증: Analysis/feed schema와 실패 시 기존 current 유지 통합 테스트.
- 위험: 실제 AI provider는 의도적으로 연결하지 않았습니다.

## Phase 6 — 분야별 정리본 PDF

- 구현: snapshot view model, HTML template, Playwright PDF, Supabase Storage 업로드, 8개 성공 뒤 snapshot 활성화.
- 검증: 8개 PDF 9페이지를 PNG로 렌더링해 한글·링크·페이지 나눔·빈 분야를 확인했습니다.
- 위험: 실제 Supabase Storage 업로드는 이 호스트에 운영 비밀값이 없어 실행하지 않았습니다.

## Phase 7 — 실제 출처 3곳

- 구현: 국회입법조사처 정적 HTML, KDI 브라우저 렌더링, 한국은행 공식 RSS, 각 list/detail fixture와 회귀 테스트, 별도 live smoke workflow.
- 검증: 외부 API 금지 자동 검사, fixture CI, 3개 실제 사이트 smoke 모두 통과.
- 위험: KDI 공개 페이지는 현재 정적 응답에도 내용이 있으나 요구한 브라우저 경로를 계속 사용합니다.

## 운영 기준 — 최근 1일 및 전국 확장 준비

- 구현: 공개·관리자·Collector의 기간 키를 `today`/`1d`로 통일했습니다. `1d`는 날짜 기반 데이터에서 오늘과 전날 발행분을 포함합니다.
- 구현: 기존 `7d` snapshot은 데이터 보존을 위해 DB에 남기고, 공개 앱은 읽지 않습니다.
- 준비: 전국 출처는 후보 카탈로그와 기관별 HTML/RSS 검증 게이트를 적용한 뒤 하나씩 fixture·adapter·smoke를 갖춰 활성화합니다.

## 전국 확장 1차 — 국토연구원

- 구현: `krihs-research` 전용 static adapter, YAML, 목록·상세 fixture, parser 회귀 test, live smoke를 추가했습니다. 공식 상세 페이지의 소개문만 읽고 내부 API 형태의 파일 URL은 호출하지 않습니다.
- 구현: Collector 설정에 `active`를 도입해 `collect --all-active`가 비활성 후보를 건너뜁니다. 국토연구원과 국회입법조사처는 현재 비활성 상태입니다.
- 검증: 국토연구원 fixture와 live smoke, source YAML schema, Collector API 금지 정책, Ruff/mypy를 통과했습니다. DB source row는 `LINK_ONLY`·`DISABLED`로 등록했습니다.
- 위험: 한국교육개발원은 공개 POST 상세 흐름 지원이 필요하고, 한국노동연구원은 공식 목록이 라이선스 오류를 반환합니다.

## 자동 발행 및 Telegram 배포

- 구현: 08:35 KST 단일 오케스트레이터, 최근 24시간 자동 품질 게이트, 시스템 승인·보류 감사 기록, 실행 이력과 Telegram outbox를 추가했습니다.
- 구현: today/1d 원자적 snapshot과 8개 정리본 생성 후 동일 snapshot으로 3,500자 이하 HTML 브리핑과 자체 정리본 PDF 한 개만 전송합니다.
- 구현: 관리 화면을 예외 검수 중심으로 바꾸고 최근 실행 수치, 단계, Telegram 상태와 실패 재시도 예약을 표시합니다.
- 안전장치: 자동 승인과 Telegram은 환경변수 기본값이 꺼져 있고, 신규 적격 문서가 없으면 기존 current snapshot을 유지합니다.
- 외부 준비: 실제 전송에는 Bot token과 별도로 대상 채널·그룹의 chat ID가 필요합니다.
