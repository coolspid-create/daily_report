# 자동 발행 및 Telegram 배포 구현 계획

> 기준 문서: `PRD.md`, `DESIGN.md`, `IMPLEMENTATION_PLAN.md`  
> 작성일: 2026-08-21  
> 목표: 최근 24시간의 신뢰 가능한 보고서를 자동 선별·발행하고 동일한 브리핑을 Telegram으로 전달한다.

## 1. 목표 운영 모델

관리자 승인을 모든 문서의 필수 관문으로 사용하지 않는다. 자동 품질 기준을 통과한 문서는 시스템이 승인하고, 기준 미달·판단 불가 문서만 관리자 예외 검수함에 남긴다.

매일 한국 시각 오전 8시 35분에 작업을 시작한다. 수집·분석·선별·스냅샷·Telegram 전달을 하나의 실행으로 순차 처리하며, 완료되는 즉시 공개한다. GitHub Actions 예약 실행은 지연될 수 있으므로 정확히 오전 9시 정각 발행을 보장하지 않고 오전 9시 전후 완료를 운영 목표로 둔다.

```text
08:35 KST 실행 시작
  -> 활성 출처 수집
  -> 최근 24시간 후보 확정
  -> 파일 검증·본문 추출·요약·중복 판정
  -> 자동 품질 게이트
       통과 -> AUTO_APPROVED
       실패/판단 불가 -> NEEDS_REVIEW
  -> 기관·분야 편중을 제한한 6~8건 선별
  -> today/1d 스냅샷과 정리본 PDF 원자적 발행
  -> 같은 스냅샷으로 Telegram 브리핑 전송
```

## 2. 확정 설계 결정

### 자동 발행과 예외 검수

- 검수 작업대는 `예외 검수함` 역할로 전환한다.
- 자동 승인 문서도 승인 정책 버전과 판정 근거를 감사 로그에 남긴다.
- 한 문서가 검수 대기로 남아도 다른 적격 문서의 발행을 막지 않는다.
- 자동 발행 실패 시 직전 정상 스냅샷을 유지한다.
- 자동 승인 정책은 환경변수로 느슨하게 바꾸지 않고 버전 관리되는 코드와 테스트로 관리한다.

### 최근 24시간의 정의

여러 기관이 시각 없이 날짜만 제공하므로 진정한 발행 시각 기준 24시간은 보장할 수 없다. MVP에서는 다음 조건을 모두 만족해야 신규 후보로 인정한다.

- `first_seen_at` 또는 문서 `created_at`이 실행 시점 기준 24시간 이내이다.
- 공식 발행일이 KST 기준 오늘 또는 전날이며 미래 날짜가 아니다.
- 발행일이 없거나 연도만 있는 자료는 자동 승인하지 않는다.
- 추후 공식 페이지가 시각을 제공하는 출처만 `published_at timestamptz` 정밀 모드로 확장한다.

### Telegram 전달 형식

- 개별 원본 PDF 파일을 일괄 업로드하지 않는다.
- Telegram에는 오늘의 스냅샷을 최종 링크를 포함해 4,000자 이하 HTML 메시지 1~2개로 나누어 보낸다.
- 각 항목은 제목, 기관, 분야, 한 문장 요약, 키워드, 공식 원문/PDF 링크를 포함한다.
- 마지막에 메타데이터·요약·링크로 만든 자체 정리본 PDF 1개만 첨부한다.
- 웹 발행과 Telegram 전달은 반드시 같은 `publication_id`와 snapshot을 사용한다.
- Telegram 실패가 웹 발행을 되돌리지 않으며 Telegram 단계만 재시도한다.

## 3. 자동 승인 정책 v1

다음 조건을 모두 통과한 문서만 자동 승인한다.

1. 출처가 `active=true`, `status=HEALTHY`이다.
2. 최근 24시간 후보 조건을 통과한다.
3. 중복 병합 대상이 아니다.
4. `rights_status`가 `LINK_ONLY` 또는 `FILE_UPLOAD_ALLOWED`이다.
5. `delivery_mode`가 `BLOCKED`가 아니다.
6. 공식 원문 URL이 정상이고 허용된 공개 URL이다.
7. `summary_status=COMPLETED`이다.
8. `summary_kind`가 `ANALYZED` 또는 `OFFICIAL_ABSTRACT`이다.
9. 실제 한 문장 이상의 요약과 1~3개 `key_tags`가 있다.
10. 분석 confidence가 초기 기준 `0.65` 이상이다.

다음 조건은 예외 검수로 보낸다.

- 발행일 누락·미래 날짜·기간 밖 날짜
- PDF 위장, 손상, 암호화, 크기 초과
- 요약 생성 실패 또는 `UNAVAILABLE`
- 공식 링크 실패 또는 세션 의존 파일 링크
- `MANUAL_REVIEW`, `BLOCKED` 권리 상태
- URL/hash/title 중복 후보
- 출처 `DEGRADED` 또는 낮은 분석 confidence

자동 승인 후 전체 피드에서는 최대 8건을 선택한다. 동일 기관은 기본 최대 2건으로 제한하고, 중요도 점수와 분야 다양성을 함께 적용한다.

### 시범 운영 정책 v2 (`2026-08-pilot-v2`)

관리자가 발행 전에 매번 검수하기 어려운 시범 운영 기간에는 아래 항목만 수동 검수로 보낸다.

- 비활성 출처
- `MANUAL_REVIEW` 또는 `BLOCKED` 권리 상태
- `BLOCKED` 전달 방식
- HTTPS가 아닌 원문 URL
- token, session, expires, signature가 포함된 세션성 파일 URL

출처 일시 저하, 날짜·요약·태그·confidence 품질 경고는 자동 승인하되 reason code를 감사 로그에 남긴다. 중복 후보는 수동 검수 없이 자동 `REJECTED` 처리한다. 이 완화는 검수 대기열을 줄이기 위한 것이며, 권리·전송·원문 추적 안전장치는 완화하지 않는다.

## 4. 데이터 마이그레이션

### 자동화 실행 기록

`automation_runs`를 추가한다.

- `id`, `scheduled_for`, `window_started_at`, `window_ended_at`
- `status`: `RUNNING`, `PUBLISHED`, `PARTIAL`, `FAILED`
- 수집·적격·자동 승인·예외·발행·전송 건수
- 현재 단계, 오류 코드, 오류 메시지, 시작·완료 시각
- 동일 예약 시각에 대한 unique constraint로 중복 실행 방지

### 자동 검수 감사 기록

`review_actions`를 확장한다.

- `actor_kind`: `ADMIN`, `SYSTEM`
- 시스템 작업에서는 `actor_id`를 nullable로 허용한다.
- action에 `AUTO_APPROVE`, `AUTO_HOLD`를 추가한다.
- `policy_version`, 판정 조건, 실패 조건을 `after_data`에 기록한다.
- 기존 관리자 감사 기록과 RLS를 보존한다.

### Telegram outbox

`telegram_deliveries`를 추가한다.

- `publication_id`, `destination_key`, `status`
- `attempt_count`, `message_ids`, `last_error`
- `created_at`, `sent_at`, `updated_at`
- `(publication_id, destination_key)` unique constraint
- `PENDING`, `SENDING`, `SENT`, `FAILED` 상태

Telegram token과 실제 chat ID는 저장하지 않는다. `destination_key`에는 비밀값이 아닌 논리 이름만 기록한다.

### 기간 계약 정리

- DB, CLI, JSON Schema, 공개 앱, workflow의 range를 `today`, `1d`로 통일한다.
- 현재 workflow의 `--range 7d` 호출을 제거한다.
- 과거 `7d` snapshot 데이터는 삭제하지 않고 비-current 이력으로 보존한다.

## 5. 구현 단계

### Phase A — 계약과 운영 기반 정리

목표: 스케줄과 기간 계약의 현재 불일치를 먼저 제거한다.

생성·수정 파일:

- `.github/workflows/collector.yml`
- `services/collector/src/report_collector/cli/main.py`
- `contracts/public-feed.schema.json`
- `supabase/migrations/0022_automation_delivery.sql`
- `.env.example`, `docs/operations.md`, `docs/deployment.md`

구현 내용:

- cron을 `35 23 * * *` UTC, 즉 08:35 KST로 변경한다.
- workflow 전체에 concurrency lock을 적용한다.
- 실패한 이전 실행과 새 실행이 겹치지 않게 한다.
- 실행 날짜는 셸의 UTC 날짜가 아니라 명시적인 `Asia/Seoul` 날짜로 계산한다.
- 수집과 발행 명령의 `today`/`1d` 계약을 통일한다.

완료 조건:

- workflow 정적 테스트에서 KST 날짜와 지원하지 않는 range 호출이 검출된다.
- 수동 `workflow_dispatch`와 예약 실행이 동일한 오케스트레이터를 사용한다.

### Phase B — 자동 품질 게이트

목표: 적격 문서는 자동 승인하고 예외만 검수함에 남긴다.

생성·수정 파일:

- `services/collector/src/report_collector/services/auto_approval_policy.py`
- `services/collector/src/report_collector/pipelines/auto_review_documents.py`
- `services/collector/src/report_collector/repositories/supabase/postgres_auto_review.py`
- `services/collector/tests/unit/test_auto_approval_policy.py`
- `services/collector/tests/integration/test_auto_review_audit.py`

구현 내용:

- DB 조회와 승인 규칙을 분리한다.
- 자동 승인 정책 결과를 구조화된 reason code 목록으로 반환한다.
- 적격 문서를 한 트랜잭션에서 승인하고 감사 로그를 기록한다.
- 자동 보류 문서는 `NEEDS_REVIEW`를 유지한다.
- 이미 승인·제외된 문서를 재실행해도 상태를 덮어쓰지 않는다.

완료 조건:

- 동일 입력은 항상 동일 판정을 내린다.
- 자동 승인 문서마다 정책 버전과 감사 기록이 존재한다.
- 권리·날짜·링크·중복·분석 실패가 자동 승인되지 않는다.

### Phase C — 일일 오케스트레이터

목표: 한 명령으로 수집부터 공개 snapshot까지 안전하게 완료한다.

생성·수정 파일:

- `services/collector/src/report_collector/cli/daily_publish_command.py`
- `services/collector/src/report_collector/pipelines/daily_publication.py`
- `services/collector/src/report_collector/repositories/supabase/postgres_automation_runs.py`
- `services/collector/src/report_collector/cli/main.py`

명령 계약:

```bash
python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 24
```

구현 내용:

- 활성 출처별 timeout과 실패 격리를 그대로 사용한다.
- 일부 출처 실패는 `PARTIAL`로 기록하되 적격 문서 발행은 계속한다.
- 자동 승인 후 ranking을 실행하고 today/1d snapshot을 생성한다.
- snapshot schema 검증과 digest 생성까지 성공한 뒤 current를 교체한다.
- 신규 적격 문서가 0건이면 빈 snapshot으로 교체하지 않고 운영 정책에 따라 직전 정상본을 유지하거나 `NO_CONTENT` 실행으로 기록한다. 초기 정책은 직전 정상본 유지로 한다.

완료 조건:

- 하나의 출처 실패가 전체 발행을 중단하지 않는다.
- 같은 예약 실행을 재시도해도 문서·승인·snapshot이 중복되지 않는다.
- snapshot 실패 시 직전 current가 유지된다.

### Phase D — Telegram provider와 메시지 구성

목표: snapshot 기반 브리핑을 안전하고 재시도 가능하게 전달한다.

생성·수정 파일:

- `services/collector/src/report_collector/providers/notifications/base.py`
- `services/collector/src/report_collector/providers/notifications/mock_provider.py`
- `services/collector/src/report_collector/providers/notifications/telegram_provider.py`
- `services/collector/src/report_collector/services/telegram_message_builder.py`
- `services/collector/src/report_collector/pipelines/deliver_publication.py`
- `services/collector/src/report_collector/repositories/supabase/postgres_delivery_repository.py`
- Telegram fixture와 단위·통합 테스트

메시지 구조:

```text
오늘의 공공리포트 | 2026.08.21
오늘 선정 7건

1. 보고서 제목
기관 · 분야 · 발행일
한 문장 요약
#키워드 #키워드
PDF | 공식 원문

오늘의 공공리포트 전체 보기
```

구현 내용:

- Telegram HTML을 안전하게 escape한다.
- 메시지는 최종 링크를 포함해 4,000자 이하에서 보고서 단위로 분할한다.
- 링크 미리보기는 기본 비활성화한다.
- 메시지 전송 후 자체 정리본 PDF를 한 번만 전송한다.
- 개별 원본 PDF 업로드 코드는 만들지 않는다.
- 429 응답의 `retry_after`, 5xx, timeout을 구분해 최대 3회 재시도한다.
- outbox를 사용해 이미 `SENT`인 publication은 다시 전송하지 않는다.
- Telegram 실패는 publication을 `FAILED`로 되돌리지 않는다.

완료 조건:

- mock provider로 실제 네트워크 없이 전체 전달 흐름을 검증한다.
- 동일 publication 재실행 시 중복 전송 요청이 발생하지 않는다.
- 링크·한글·특수문자·메시지 분할이 Telegram HTML 규칙을 만족한다.

### Phase E — 관리자 예외 검수 UI

목표: 관리자가 자동화 상태와 예외만 빠르게 확인한다.

생성·수정 파일:

- `apps/web/features/admin-review/components/review-workbench.tsx`
- `apps/web/features/admin-review/components/automation-status.tsx`
- `apps/web/features/admin-review/server/get-automation-status.ts`
- 필요한 관리자 Route Handler

구현 내용:

- 헤더를 `예외 검수` 중심으로 변경한다.
- 최근 자동 실행 시각, 수집 수, 자동 승인 수, 예외 수, Telegram 상태를 표시한다.
- 수동 승인·제외 기능은 유지한다.
- 실패한 Telegram delivery만 재시도하는 관리자 액션을 제공한다.
- 공개 화면에는 자동화·Telegram 관리 기능을 노출하지 않는다.

완료 조건:

- 정상 자동 승인 문서는 검수 목록에 나타나지 않는다.
- 예외 reason code가 관리자에게 이해 가능한 한국어로 표시된다.
- 비관리자는 자동화 상태와 재시도 API에 접근할 수 없다.

### Phase F — 배포와 점진 활성화

1. `DRY_RUN=true`로 3일간 수집·판정만 실행하고 자동 승인 결과를 저장하지 않는다.
2. 기존 관리자 판단과 자동 정책 결과를 비교한다.
3. 비공개 Telegram 채팅에 mock이 아닌 실제 Bot으로 시험 전송한다.
4. 자동 승인을 켜되 Telegram은 시험 채팅으로 유지한다.
5. 웹 snapshot 결과를 3일 확인한 뒤 실제 채널로 전환한다.
6. 실패율과 오탐이 기준을 넘으면 자동 승인을 끄고 예외 검수 모드로 즉시 복귀한다.

## 6. 환경변수와 비밀값

추가 환경변수:

```text
AUTOMATION_TIMEZONE=Asia/Seoul
AUTOMATION_WINDOW_HOURS=24
AUTO_APPROVAL_ENABLED=false
AUTO_APPROVAL_POLICY_VERSION=2026-08-pilot-v2
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_DESTINATION_KEY=daily-report-main
TELEGRAM_MAX_ATTEMPTS=3
```

- Bot token과 chat ID는 GitHub Actions secret 또는 Collector 배포 환경에만 둔다.
- Web의 `NEXT_PUBLIC_*` 환경변수에 Telegram 비밀값을 넣지 않는다.
- 로그, DB 오류 메시지, snapshot에 Bot token을 기록하지 않는다.

## 7. 필수 테스트

- KST 24시간 경계와 날짜만 제공하는 출처
- 누락·과거·미래 발행일 자동 보류
- 활성/비활성 및 HEALTHY/DEGRADED 출처 판정
- 권리 상태와 delivery mode별 자동 승인 차단
- 분석 confidence, summary kind, key tag 검증
- URL/hash/title 중복 자동 보류
- 자동 승인 감사 기록과 정책 버전
- 기관별 최대 2건 및 전체 최대 8건 선별
- 일부 출처 timeout 후 다음 출처 진행
- today/1d snapshot schema와 원자적 교체
- snapshot 실패 시 직전 정상 버전 유지
- Telegram HTML escape와 최종 링크를 포함한 4,000자 분할
- Telegram 429/5xx/timeout 재시도
- 정리본 PDF 1회 전송과 개별 원본 PDF 미전송
- 동일 publication 중복 전달 방지
- 익명/admin 자동화 상태 및 재시도 RLS
- cron KST 변환, 잘못된 range와 누락 secret 정적 검사
- 전체 fixture 기반 `collect -> auto review -> snapshot -> Telegram mock` E2E

## 8. 품질 게이트

- `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`
- Ruff, mypy, 전체 pytest
- migration/RLS 및 JSON Schema 검증
- `verify-file-sizes.py`
- Collector 외부 콘텐츠 API 금지 검사 유지
- Telegram API는 전달 전용 provider에서만 호출됨을 정책 검사로 확인
- skip이나 임시 TODO 없이 DRY_RUN 전체 흐름 실행

## 9. 완료 조건

- 예약 실행 한 번으로 최근 24시간 수집부터 웹 발행까지 완료된다.
- 적격 문서는 관리자 개입 없이 공개되고 예외만 검수함에 남는다.
- 웹과 Telegram의 보고서 ID와 순서가 동일하다.
- Telegram에는 브리핑 텍스트와 자체 정리본 PDF만 전달된다.
- 재실행·재시도에도 snapshot과 Telegram 메시지가 논리적으로 중복되지 않는다.
- Telegram 장애가 웹 공개를 훼손하지 않는다.
- 자동 승인과 시스템 보류의 근거를 DB에서 추적할 수 있다.

## 10. 구현 전 필요한 외부 준비

- BotFather에서 생성한 Telegram Bot token
- Bot을 관리자로 추가한 대상 채널 또는 그룹
- 대상 `chat_id` 또는 공개 채널 username
- GitHub Actions 또는 Collector 배포 환경의 secret 등록 권한

이 값들은 Phase D의 mock·단위 테스트가 끝난 뒤 실제 시험 전송 단계에서만 필요하다.
