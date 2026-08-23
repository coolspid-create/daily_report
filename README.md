# 오늘의 공공리포트

정부·국회·공공 연구기관의 공개 보고서를 HTML/RSS/정상 브라우저 렌더링으로 수집하고, 관리자 승인 후 스냅샷으로 공개하는 경량 서비스입니다. 공개 사용자는 `/` 한 화면에서 전체와 7개 분야를 전환하고 공식 파일 또는 공식 출처로 이동합니다.

## 구성

- `apps/web`: Next.js 16 App Router 공개 피드와 관리자 검수대
- `services/collector`: Python 3.12+ 수집·검증·분석·발행·PDF CLI
- `contracts`: source, analysis, public feed JSON Schema
- `supabase`: PostgreSQL migration, seed, RLS 테스트
- `config/sources`: 실제 출처 3곳의 YAML

## 요구 사항과 설치

Node.js 20.9+, pnpm 11, Python 3.12+, Supabase CLI/Docker가 필요합니다.

```bash
corepack enable
pnpm install
python -m venv .venv
./.venv/Scripts/python -m pip install -e "./services/collector[dev]"
./.venv/Scripts/python -m playwright install chromium
```

PowerShell에서는 이후 `.\.venv\Scripts\Activate.ps1`로 가상환경을 활성화합니다. macOS/Linux에서는 실행 파일 경로를 `.venv/bin/python`으로 바꾸고 `source .venv/bin/activate`를 사용합니다. `.env.example`을 `.env`로 복사하고 실제 비밀값을 채우되 커밋하지 않습니다.

## 데이터베이스와 로컬 실행

```bash
supabase start
supabase db reset
pnpm dev
```

웹은 `http://localhost:3000`에서 열립니다. Supabase가 없는 개발 환경에서는 공개 화면만 `apps/web/data/public-snapshots.json` fixture를 읽습니다. 관리 기능은 실제 Supabase Auth와 DB가 있어야 동작합니다.

Collector 컨테이너는 `docker compose run --rm collector`로 CLI 도움말까지 확인할 수 있습니다. 호스트의 `.data`, `config`, `contracts`만 명시적으로 연결합니다.

## Collector CLI

```bash
python -m report_collector collect --source nars
python -m report_collector collect --all-active
python -m report_collector build-snapshot --date 2026-08-21 --range 7d
python -m report_collector build-digest --date 2026-08-21 --topic all --range 7d
python -m report_collector build-digest --date 2026-08-21 --topic all --range 7d --snapshot-file apps/web/data/public-snapshots.json
python -m report_collector cleanup --expired-files
python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168 --dry-run
python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168
```

외부 출처 수집은 공개 HTML, 공식 RSS, 정상 브라우저 렌더링만 사용합니다. 외부 API, JSON/XHR 엔드포인트 직접 호출, 로그인·CAPTCHA 우회는 허용하지 않습니다.

`build-snapshot`은 전체+7개 분야 PDF 생성과 Supabase Storage 업로드가 모두 성공한 뒤에만 새 snapshot을 current로 전환합니다. 로컬 템플릿 확인만 필요하면 `build-digest --snapshot-file`을 사용합니다.

## 검증

```bash
pnpm verify
ruff check services scripts
mypy services/collector/src
pytest
supabase test db
```

실제 사이트 smoke는 기본 테스트에서 제외하며 `pytest -m live services/collector/tests/live`로 별도 실행합니다. 테스트를 통과시키기 위한 `skip`은 사용하지 않습니다.

## 환경변수

- 공개 웹: `NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- 서버/관리자: `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_ALLOWED_EMAILS`
- Vercel Cron: `CRON_SECRET`, `GITHUB_ACTIONS_DISPATCH_TOKEN`, `GITHUB_REPOSITORY`, `GITHUB_COLLECTOR_WORKFLOW`, `GITHUB_COLLECTOR_REF`, `FEED_REVALIDATION_SECRET`
- Collector/DB: `DATABASE_URL`, `SUPABASE_URL`, `TEMP_FILE_DIR`, `MAX_DOWNLOAD_BYTES`, `DEFAULT_REQUEST_DELAY_MS`, `PLAYWRIGHT_ENABLED`, `TEMP_FILE_TTL_HOURS`
- 분석: `ANALYSIS_PROVIDER`, `ANALYSIS_API_KEY`, `ANALYSIS_MODEL`
- Storage: `DIGEST_BUCKET`, `TEMP_BUCKET`, `MIRROR_BUCKET`
- 자동 발행: `AUTOMATION_TIMEZONE`, `AUTOMATION_WINDOW_HOURS`(기본 168시간), `AUTO_APPROVAL_ENABLED`, `AUTO_APPROVAL_POLICY_VERSION`, `PUBLIC_WEB_URL`
- Telegram(Collector 전용): `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_DESTINATION_KEY`, `TELEGRAM_MAX_ATTEMPTS`

`SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, AI 키와 Telegram 값은 브라우저에 노출하면 안 됩니다. `GITHUB_ACTIONS_DISPATCH_TOKEN`은 Vercel 서버에서만 사용하며 Actions workflow 실행 권한만 부여합니다. 기본 분석 provider는 외부 호출이 없는 `mock`입니다. 자동 승인은 기본값이 꺼져 있으며 `--dry-run`으로 정책 결과를 먼저 확인합니다.

GitHub Actions에서는 민감한 값(`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `FEED_REVALIDATION_SECRET`)을 repository secret으로, `AUTO_APPROVAL_ENABLED`, `TELEGRAM_ENABLED`, `PUBLIC_WEB_URL`을 repository variable로 설정합니다. 발행 완료 후 workflow는 인증된 재검증 경로를 호출하여 공개 피드 캐시를 즉시 비웁니다.

운영 세부사항은 `docs/source-adapter-guide.md`, `docs/rights-policy.md`, `docs/operations.md`, `docs/deployment.md`를 참고합니다.
