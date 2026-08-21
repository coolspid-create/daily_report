# IMPLEMENTATION PLAN — 오늘의 공공리포트

> 후속 운영 자동화 계획: `AUTOMATED_PUBLISHING_PLAN.md`

> 기준 문서: `PRD.md`, `DESIGN.md`  
> 작성일: 2026-08-21  
> 원칙: 공개 한 페이지, 공식 링크 우선, 관리자 승인, 작은 도메인 모듈

## 1. 기준 문서와 충돌 점검

- 첨부 PRD의 실제 파일명은 `PRD(20260821-025000).md`이다. 구현 시작 시 같은 내용을 루트 `PRD.md`로 두어 DESIGN이 참조하는 기준 파일명을 맞춘다.
- PRD는 실제 출처를 3~5곳으로 시작하도록 하고 이번 요청은 우선 3곳으로 한정한다. 충돌이 아니라 범위 구체화이므로 정확히 3곳만 연결한다.
- PRD의 개발 Phase 구분과 이번 요청의 Phase 0~7 구분은 산출물 묶음만 다르다. 의존 순서는 같으므로 이번 요청의 Phase 0~7을 실행 순서로 사용한다.
- PRD의 최근 7일 지연 로드는 선택 사항이다. 공개 UI 단순성과 즉시 반응 요구를 우선해 오늘/최근 7일 스냅샷을 최초 데이터에 함께 포함할 수 있는 계약으로 구현한다.
- 외부 콘텐츠 수집은 공개 HTML, 공식 RSS/Atom, 공개 첨부파일, 정상 브라우저 렌더링만 허용한다. 내부 Supabase/Route Handler 통신은 이 금지 범위에 포함되지 않는다.
- 공개 상세 페이지, 공개 인증, 마이페이지, 상세검색, AI 채팅, 자체 PDF 뷰어, 통계 대시보드는 만들지 않는다.

## 2. 단계별 구현 계획

### Phase 0 — 기반

목표: 독립적으로 검사 가능한 monorepo, 계약, DB, 로컬 실행 기반을 만든다.

생성·수정 파일:

- 루트: `PRD.md`, `package.json`, `pnpm-workspace.yaml`, `pyproject.toml`, `.env.example`, `.gitignore`, `docker-compose.yml`
- Web: `apps/web/package.json`, `tsconfig.json`, `next.config.ts`, ESLint/Vitest 설정, 최소 App Router 파일
- Collector: `services/collector/pyproject.toml`, 패키지 엔트리포인트와 설정 모듈
- 계약: `contracts/public-feed.schema.json`, `analysis-result.schema.json`, `source-config.schema.json`
- DB: `supabase/migrations/0001`~`0007`, `supabase/seed.sql`, `supabase/tests/rls.sql`
- 자동화: `scripts/verify-file-sizes.py`, source/contract 검사 스크립트, `.github/workflows/ci.yml`

데이터 마이그레이션:

- sources/runs/items, documents/sources/files, analysis/topics, review/publication/snapshot/digest, RLS를 책임별 migration으로 분리한다.
- 7개 topic을 seed하고 `LINK_ONLY`를 권리 기본값으로 둔다.

테스트:

- JSON Schema 자체 유효성, source YAML 검증, migration/RLS 정적 계약, 파일 크기 검사.

완료 조건:

- 패키지 설치 후 TypeScript/Python 기본 lint/typecheck/test가 실행되고 파일 크기 검사와 계약 검증이 CI에 포함된다.

### Phase 1 — Collector 핵심

목표: 로컬 fixture만으로 정적 HTML, 렌더링 HTML, RSS를 발견·상세 해석할 수 있게 한다.

생성·수정 파일:

- `adapters/base.py`, `adapters/generic/{static_board,rendered_board,rss_feed}.py`
- `config/source_config.py`, `providers/http/http_client.py`, `providers/browser/playwright_browser.py`
- `pipelines/collect_source.py`, `repositories/*`, `cli/collect_command.py`
- `config/sources/*.yaml`, `services/collector/tests/fixtures/{html,rss}` 및 parser 테스트

데이터 마이그레이션: Phase 0의 source cursor/run 테이블을 사용하며 추가 변경은 없다.

테스트:

- YAML schema, 목록/상세 fixture, cursor, retry/timeout/delay 설정, URL 보안, API·숨은 JSON/XHR 미사용 정책 검사.

완료 조건:

- 가상 출처 2곳과 RSS fixture가 네트워크 없이 결정론적으로 수집되고 서로 독립된 config/adapter 경계를 유지한다.

### Phase 2 — 문서 처리

목표: 파일 안전성, PDF 추출, 중복, 상태 머신, 임시 보존 정책을 구현한다.

생성·수정 파일:

- `services/{file_validation,deduplication,rights,workflow}_service.py`
- `extractors/{pdf_metadata,pdf_text}_extractor.py`, `pipelines/process_document.py`
- `cli/cleanup_command.py`, PDF fixture와 단위 테스트

데이터 마이그레이션: document file expiry/text retention 필드를 Phase 0 schema와 대조하고 필요 시 보정 migration을 추가한다.

테스트:

- 정상/손상/HTML 위장 PDF, SHA-256, URL/hash/title 중복, 허용/비허용 상태 전이, TTL cleanup.

완료 조건:

- 검증 실패 파일은 분석되지 않고, 기본 48시간 TTL이 적용되며, `LINK_ONLY` 기본 권리 정책이 전달 모드로 일관되게 변환된다.

### Phase 3 — 관리자 검수

목표: Supabase Auth 기반 `/admin/login`과 `/admin` 단일 작업대를 구현한다.

생성·수정 파일:

- `app/admin/login/page.tsx`, `app/admin/page.tsx`, `features/admin-review/**`, `features/source-health/**`
- 관리자 Route Handler, `lib/auth/**`, `lib/database/**`

데이터 마이그레이션: admin allowlist/claim 판정과 review audit 저장 정책을 RLS에 반영한다.

테스트:

- 익명/관리자 권한, 입력 schema, approve/hold/reject/update/merge, source enable/disable, 감사 기록.

완료 조건:

- 비관리자는 데이터와 쓰기 작업에 접근하지 못하고, 관리자는 상세 페이지 이동 없이 검수·병합·출처 상태 변경을 수행한다.

### Phase 4 — 공개 한 페이지 피드

목표: `/`에서 받은 스냅샷만으로 분야와 기간을 즉시 전환하고 정확한 전달 버튼을 표시한다.

생성·수정 파일:

- `app/(public)/page.tsx`, `features/public-feed/{components,hooks,lib,server,types,constants}/**`
- CSS token과 접근성/반응형 스타일, 공개 snapshot fixture

데이터 마이그레이션: 없음.

테스트:

- topic click, URL query, localStorage 복원, range 전환, empty state, delivery mode별 버튼과 외부 링크 속성.

완료 조건:

- 공개 내부 상세 route 없이 모바일 한 열 피드가 동작하고, 분야 전환에 추가 네트워크 요청이 없다.

### Phase 5 — 분석·선별·스냅샷

목표: mock 분석, 순위, 승인 전용 원자적 snapshot 발행을 구현한다.

생성·수정 파일:

- `providers/ai/{base,mock_provider}.py`, `services/{summarization,ranking,publication}_service.py`
- `pipelines/publish_snapshot.py`, `cli/snapshot_command.py`, 계약/통합 테스트

데이터 마이그레이션: current snapshot 단일성 및 원자적 포인터 교체 함수/RPC를 추가한다.

테스트:

- AnalysisResult schema, 승인 문서만 포함, 분야/기관 제한, snapshot schema, 생성 실패 시 직전 current 유지.

완료 조건:

- 공개 앱은 document 테이블을 읽지 않고 검증된 current snapshot만 읽는다.

### Phase 6 — 분야별 정리본 PDF

목표: 전체+7개 분야에 대한 링크 포함 요약 PDF를 snapshot에서 생성한다.

생성·수정 파일:

- `digest/{digest_builder,digest_view_model,digest_renderer,digest_storage}.py`
- `digest/templates/{digest.html.j2,digest.css}`, `cli/digest_command.py`, digest 테스트

데이터 마이그레이션: digest 저장 상태/체크섬 필드는 기존 migration을 사용한다.

테스트:

- view model, HTML 링크, 8개 PDF 생성, 원본 병합 부재, 실패 시 공개 digest 포인터 미교체.

완료 조건:

- Playwright가 설치된 환경에서 8개 PDF를 만들며, 미설치 환경은 명시적 오류로 실패한다.

### Phase 7 — 실제 출처 3곳

목표: 구조가 다른 공개 출처 3곳을 정책 확인 후 별도 smoke workflow로 연결한다.

생성·수정 파일:

- 출처별 `config/sources/*.yaml`, 필요 시 `adapters/sources/<source>/parser.py`
- 각 출처 list/detail fixture 및 회귀 테스트, `.github/workflows/source-smoke.yml`
- `docs/source-adapter-guide.md`와 정책 근거 기록

데이터 마이그레이션: `sources` seed에 3개 출처를 추가한다.

테스트:

- fixture 회귀는 기본 CI, 실제 공개 페이지는 수동/저빈도 smoke에서만 실행한다.

완료 조건:

- 정적 HTML 1곳, 브라우저 렌더링 1곳, 공식 RSS 또는 repository형 1곳이 독립 config/fixture로 존재하며 API/XHR 직접 호출이 없다.

## 3. 공통 문서와 검증

- `README.md`: 설치, 환경변수, migration, 로컬 실행, 테스트/build, collector CLI.
- `docs/source-adapter-guide.md`: config와 전용 parser 선택 기준, fixture/smoke 규칙.
- `docs/rights-policy.md`: 권리 상태, delivery mode, TTL, 링크 우선.
- `docs/operations.md`: 수집/링크/snapshot 실패, rollback, cleanup.
- `docs/deployment.md`: Vercel, Supabase, Collector 배포와 secret 경계.
- 각 Phase 종료 시 `IMPLEMENTATION_STATUS.md`에 구현, 변경 파일, 검증, 남은 위험을 기록한다.

최종 품질 게이트:

1. `pnpm typecheck`, `pnpm lint`, `pnpm test`, `pnpm build`
2. Python Ruff, mypy, pytest
3. JSON Schema/source config validation
4. migration/RLS test
5. `python scripts/verify-file-sizes.py`
6. 공개 route 구조 감사와 금지 패턴 검사
7. 브라우저에서 `/`, topic/range/localStorage/delivery actions, `/admin/login` 접근 확인

## 4. 계획 자체 점검

- 공개 화면은 `/` 한 페이지뿐이며 공개 문서 상세 route를 계획하지 않았다.
- 수집 API 금지와 정상 브라우저 렌더링 경계를 adapter/config/test/workflow에 반영했다.
- `page.tsx`, Route Handler, CLI는 조립 계층으로 유지하고 규칙은 feature/service에 둔다.
- 승인 전용 snapshot과 실패 시 직전 버전 유지가 데이터/서비스/테스트에 모두 포함됐다.
- 권리 미확인 원본은 `LINK_ONLY`, 임시 파일은 기본 48시간으로 두고 cleanup을 포함했다.
- 실제 출처는 정확히 3곳이며 live 검증은 기본 CI와 분리했다.
- 문서가 요구한 기능과 품질 게이트를 TODO나 skip으로 비우지 않는다.
