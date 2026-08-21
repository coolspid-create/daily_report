# Codex 구현 프롬프트 — 오늘의 공공리포트

아래 프롬프트를 저장소 루트에서 Codex에 전달합니다. 저장소 루트에 `PRD.md`와 `DESIGN.md`를 함께 둔 상태를 전제로 합니다.

---

## 메인 프롬프트

```text
프로젝트명: 오늘의 공공리포트

저장소 루트의 PRD.md와 DESIGN.md를 먼저 처음부터 끝까지 읽고, 두 문서를 제품 요구사항과 기술 설계의 단일 기준으로 사용해 주세요.

목표는 정부기관, 국회기관, 공공 연구기관, 국책연구기관 및 공개 리포트를 발간하는 주요 기관의 공개 웹페이지에서 신규 보고서를 수집하고, 중복 제거·분류·요약·관리자 검수를 거쳐, 사용자가 관심 분야를 한 번 클릭하는 것만으로 오늘의 선정 보고서와 공식 파일을 받을 수 있는 경량 웹 서비스를 구축하는 것입니다.

가장 중요한 제품 제약:
1. 공개 사용자 화면은 사실상 `/` 한 페이지뿐입니다.
2. 관심 분야를 누르면 같은 화면에서 목록만 즉시 변경되어야 합니다.
3. 공개 보고서 상세 페이지를 만들지 마세요.
4. 보고서 카드 안에서 제목, 기관, 날짜, 파일정보, 왜 볼 만한가, 핵심 3개, 파일 버튼을 모두 확인할 수 있어야 합니다.
5. 공개 회원가입, 마이페이지, 상세검색, AI 채팅, 자체 PDF 뷰어, 통계 대시보드를 만들지 마세요.
6. 외부 콘텐츠 수집에는 API를 사용하지 마세요. 공식·비공식 API, 숨겨진 JSON/XHR 엔드포인트 직접 호출도 금지합니다.
7. 허용되는 수집 방식은 공개 HTML, 공식 RSS/Atom, 공개 첨부파일 링크, 정상적인 브라우저 렌더링뿐입니다.
8. 로그인·유료·CAPTCHA·접근 제한을 우회하지 마세요.
9. 원본 파일은 권리 확인 없이 영구 저장하지 말고 공식 파일 URL 또는 공식 상세 페이지 연결을 우선하세요.
10. 공개 화면에서 AI를 실시간 호출하지 말고, 수집 파이프라인에서 미리 생성한 결과만 사용하세요.

코드 구조의 절대 규칙:
1. 파일 하나에 코드를 몰아넣지 마세요.
2. TypeScript/Python 로직 파일은 원칙적으로 250줄 이하, 350줄 초과 금지입니다.
3. React 컴포넌트는 원칙적으로 150줄 이하, 220줄 초과 금지입니다.
4. 함수는 원칙적으로 40줄 이하, 70줄 초과 금지입니다.
5. page.tsx와 Route Handler는 조립·검증·서비스 호출만 담당하게 하세요.
6. 비즈니스 로직을 React 컴포넌트, Route Handler, CLI 엔트리포인트에 넣지 마세요.
7. 모든 출처를 하나의 collector.py 또는 switch 문에 넣지 마세요.
8. `utils.ts`, `helpers.py`, `common.py` 같은 범용 쓰레기통 파일을 만들지 마세요.
9. 파일을 나눌 때는 도메인 책임을 기준으로 나누고, 의미 없는 1~2줄 wrapper를 남발하지 마세요.
10. `scripts/verify-file-sizes.py`를 만들어 CI에서 크기 제한을 검사하세요.

권장 기술 구성은 DESIGN.md를 따르세요.
- Web: Next.js App Router + TypeScript strict + Tailwind 또는 작은 CSS 토큰
- 관리자 인증: Supabase Auth
- DB/Storage: Supabase PostgreSQL/Storage
- Collector: Python 3.12+, httpx, BeautifulSoup/selectolax, Playwright, PyMuPDF, Pydantic, pytest
- 스케줄과 배포에 종속되지 않는 CLI 기반 Collector
- AI 분석은 provider interface 뒤에 두고 mock provider를 먼저 구현

반드시 먼저 할 일:
1. PRD.md와 DESIGN.md의 요구사항 충돌 여부를 검토하세요.
2. 저장소가 비어 있거나 초기 상태라면 DESIGN.md의 파일 트리를 기준으로 최소 골격을 만드세요.
3. `IMPLEMENTATION_PLAN.md`를 작성하세요.
4. 계획에는 단계별 목표, 생성·수정 파일, 데이터 마이그레이션, 테스트, 완료 조건을 포함하세요.
5. 계획이 문서와 충돌하지 않는지 스스로 점검한 뒤 구현을 시작하세요.

구현 순서:

Phase 0 — 기반
- monorepo 골격 생성
- .env.example
- TypeScript/Python lint, typecheck, test 설정
- contracts JSON Schema
- Supabase migrations와 7개 topic seed
- Docker/로컬 실행 기반
- 파일 크기 검사 스크립트

Phase 1 — Collector 핵심
- SourceAdapter 인터페이스
- StaticBoardAdapter
- RenderedBoardAdapter
- RssAdapter
- source config YAML schema와 validator
- 로컬 HTML/PDF fixture 기반 가상 출처 2곳
- source run, cursor, retry, timeout, request delay
- API나 숨은 JSON 엔드포인트를 사용하지 않았는지 테스트와 문서로 확인

Phase 2 — 문서 처리
- 첨부파일 발견
- MIME/헤더/크기/암호화 검증
- SHA-256
- PDF 메타·텍스트 추출
- URL, hash, normalized title 기반 중복 제거
- workflow state machine
- 임시 파일 TTL와 cleanup command

Phase 3 — 관리자 검수
- `/admin/login`
- `/admin` 한 화면 검수 작업대
- 검수 목록과 인라인 작업 패널
- 제목, 기관, 날짜, 대표 분야, 왜 볼 만한가, 핵심 3개, delivery mode 수정
- 승인, 보류, 제외
- 중복 후보 병합
- 출처 상태 전환
- 관리자 외 접근 차단과 RLS 테스트

Phase 4 — 공개 한 페이지 피드
- `/` 단일 공개 화면
- 전체 + 7개 분야 버튼
- 오늘/최근 7일
- localStorage 관심 분야 복원
- URL query 동기화
- ReportCard, ReportActions, EmptyFeed
- 직접 공식 파일, 공식 페이지, 자체 허용 파일, 요약 전용 상태에 따른 정확한 버튼
- 내부 상세 페이지를 절대 추가하지 않기

Phase 5 — 분석·선별·스냅샷
- AnalysisProvider interface
- MockAnalysisProvider
- 구조화된 AnalysisResult와 schema validation
- ranking service
- 관리자 승인 문서만 포함하는 feed snapshot
- snapshot 생성 실패 시 직전 정상 버전 유지
- 공개 앱은 개별 문서 테이블이 아니라 snapshot만 읽기

Phase 6 — 분야별 정리본 PDF
- snapshot 기반 view model
- HTML template
- Playwright print-to-PDF
- 전체 + 7개 분야 파일 생성
- 원본 PDF 병합 금지
- 정리본에 공식 출처와 파일 링크 포함

Phase 7 — 실제 출처 3곳
- 구조가 서로 다른 공개 출처 3곳만 먼저 구현
- 최소 1곳은 정적 HTML 게시판
- 최소 1곳은 브라우저 렌더링이 필요한 공개 페이지
- 최소 1곳은 공식 RSS 또는 리포지터리형 공개 페이지
- 각 출처마다 list/detail fixture와 parser 회귀 테스트 작성
- 실제 사이트 테스트는 기본 CI에서 실행하지 말고 별도 smoke workflow로 분리

공개 UI 세부 조건:
- 모바일 우선, 한 열
- 사이드바, 햄버거, 하단 내비게이션 없음
- 분야 버튼은 모바일 가로 스크롤
- 표지 이미지 기본 미사용
- 카드 클릭 전체 링크 금지
- 기본 액션은 파일 받기, 보조 액션은 공식 출처
- 분야 전환 시 이미 받은 스냅샷을 필터링하여 네트워크 대기 없이 반응
- 접근성: button, aria-pressed, keyboard focus, 외부 링크 안내

데이터·권리 조건:
- delivery mode: DIRECT_OFFICIAL_FILE, OFFICIAL_PAGE_ONLY, MIRRORED_ALLOWED, SUMMARY_ONLY, BLOCKED
- rights status: FILE_UPLOAD_ALLOWED, LINK_ONLY, MANUAL_REVIEW, BLOCKED
- LINK_ONLY를 기본값으로 사용
- 세션 의존·만료형 파일 URL은 OFFICIAL_PAGE_ONLY로 처리
- 원본 임시 파일은 기본 24~72시간 TTL
- 분석을 마친 전체 추출 텍스트도 불필요하게 장기 보관하지 않기

테스트 필수 항목:
- source YAML schema validation
- 정적·렌더링 adapter parser
- 정상 PDF, 손상 PDF, HTML 위장 PDF
- hash/title/url 중복 판정
- workflow state transition
- AnalysisResult schema
- feed snapshot schema
- topic click과 localStorage 복원
- delivery mode별 버튼
- anonymous/admin RLS
- 관리자 승인 후 snapshot 반영
- snapshot 실패 시 이전 버전 유지
- 파일 크기 규칙 검사

품질 게이트:
- pnpm typecheck/lint/test/build 통과
- Python lint/typecheck/pytest 통과
- migration과 RLS test 통과
- JSON Schema validation 통과
- verify-file-sizes 통과
- 테스트를 skip하거나 임시 비활성화하여 통과시키지 말 것
- TODO로 핵심 기능을 비워두지 말 것

문서 산출물:
- README.md: 설치, 환경변수, 마이그레이션, 로컬 실행, 테스트, build, collector CLI
- docs/source-adapter-guide.md: 새 출처 추가 방법
- docs/rights-policy.md: 파일 전달 모드와 권리 상태
- docs/operations.md: 수집 실패, 링크 실패, snapshot rollback, cleanup 절차
- docs/deployment.md: Vercel, Supabase, Collector 배포

작업 방식:
- 작은 단계로 구현하고 각 단계마다 테스트를 실행하세요.
- 기존 파일을 수정하기 전에 현재 구조와 의도를 먼저 읽으세요.
- 한 단계가 끝날 때마다 구현한 내용, 변경 파일, 테스트 결과, 남은 위험을 기록하세요.
- 요구사항이 모호할 때는 공개 화면 단순성, 공식 링크 우선, 관리자 승인, 작은 모듈을 우선하는 결정을 하세요.
- 최신 라이브러리 사용법이 필요하면 해당 공식 문서만 확인하고, 버전은 구현 시점의 안정 버전을 사용하세요.

완료 시 최종 보고 형식:
1. 구현 요약
2. 최종 파일 트리
3. 주요 설계 결정
4. 구현된 사용자 흐름
5. 구현된 Collector 흐름
6. 테스트·빌드 결과와 실행 명령
7. 환경변수 목록
8. 아직 연결하지 않은 실제 출처와 이유
9. 알려진 제한사항
10. 다음 권장 단계

먼저 PRD.md, DESIGN.md를 읽고 IMPLEMENTATION_PLAN.md를 작성한 뒤, Phase 0부터 순서대로 구현을 시작하세요.
```

---

## 권장 사용 방법

1. 새 저장소 루트에 `PRD.md`, `DESIGN.md`, `CODEX_PROMPT.md`를 둡니다.
2. 위 메인 프롬프트를 Codex에 전달합니다.
3. Codex가 만든 `IMPLEMENTATION_PLAN.md`를 먼저 검토합니다.
4. 공개 화면에 상세 페이지, 회원가입, 복잡한 검색이 추가되지 않았는지 확인합니다.
5. 초기 실제 출처는 3곳만 연결하고, fixture 테스트가 안정된 뒤 5곳으로 늘립니다.
6. 첫 배포 후 수집 성공률과 파일 클릭률을 확인한 뒤 20~25개 출처로 확장합니다.

---

## 구현 후 검수용 후속 프롬프트

```text
현재 저장소가 PRD.md와 DESIGN.md를 실제로 준수하는지 감사를 수행해 주세요.

특히 아래 항목을 코드와 실행 결과로 검증하세요.

1. 공개 경로가 `/` 한 페이지 중심인지
2. 내부 보고서 상세 페이지가 추가되지 않았는지
3. 관심 분야 클릭이 페이지 이동 없이 동작하는지
4. 공개 회원가입·마이페이지·상세검색·AI 채팅이 없는지
5. 외부 콘텐츠 수집에 API, 숨은 JSON/XHR 엔드포인트를 사용하지 않았는지
6. 파일 하나가 350줄을 넘거나 컴포넌트가 220줄을 넘지 않는지
7. page.tsx, Route Handler, collector entrypoint에 비즈니스 로직이 몰리지 않았는지
8. 모든 출처가 독립 adapter/config/fixture 구조인지
9. 공개 앱이 승인된 snapshot만 읽는지
10. 권리 불명확 자료가 LINK_ONLY 기본값인지
11. 원본 임시 파일과 추출 텍스트의 보존 기간이 제한되는지
12. snapshot 생성 실패 시 직전 버전이 유지되는지
13. 테스트가 실제로 실행되고 skip으로 우회되지 않았는지
14. RLS와 관리자 권한이 올바른지
15. README의 명령으로 신규 환경에서 실행 가능한지

발견한 문제를 심각도 Critical, High, Medium, Low로 분류하고, 각 문제마다 관련 파일과 수정 방법을 제시하세요.
Critical과 High 문제는 직접 수정하고 전체 테스트를 다시 실행하세요.
마지막에 준수 여부를 표로 정리하고 남은 위험을 명시하세요.
```
