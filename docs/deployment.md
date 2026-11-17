# 배포 가이드

## Supabase

1. 별도 프로젝트를 만들고 `supabase/migrations`와 `supabase/seed.sql`을 적용합니다.
2. `supabase test db`로 익명/관리자 RLS를 검증합니다.
3. 관리자 사용자의 `app_metadata.role`을 `admin`으로 설정하고 `ADMIN_ALLOWED_EMAILS`도 방어적으로 구성합니다.
4. 공개 앱에는 anon key만, 웹 서버와 Collector에는 service role/DB 접속값만 둡니다.
5. Storage bucket은 digest 공개 정책과 임시/미러 원본의 비공개 정책을 분리합니다.

## Vercel Web

Vercel Project Root Directory를 `apps/web`으로 지정합니다. `next.config.ts`의 `output: "standalone"`은 Docker 전용이므로 Vercel 배포에서는 사용하지 않습니다. `NEXT_PUBLIC_*`만 브라우저 공개 값으로 넣고 service role은 서버 환경에만 둡니다. 배포 후 `/`, `/admin/login`, `/api/health`, 외부 링크 속성을 확인합니다.

정기 수집은 GitHub Actions의 `collector.yml`과 Vercel Cron에 함께 예약합니다. Vercel은 `CRON_SECRET`으로 요청을 확인하고 수집 저장소에만 설치한 GitHub App의 단기 토큰으로 워크플로를 실행합니다. App에 Actions 읽기 및 쓰기 권한을 부여하고 `GITHUB_COLLECTOR_APP_ID`, `GITHUB_COLLECTOR_INSTALLATION_ID`, `GITHUB_COLLECTOR_APP_PRIVATE_KEY_BASE64`를 Vercel Production에 등록합니다. 기존 수동 호출에는 `GITHUB_ACTIONS_DISPATCH_TOKEN`도 지원합니다. 공개 피드 갱신에는 `FEED_REVALIDATION_SECRET`을 사용합니다.

## Collector

리포트는 평일 08:35 KST에 `daily-publish --scheduled-run`으로, 보도자료는 평일 10:30 KST에 `collect-press`로 실행합니다. 백업 확인 시각은 리포트 09:25, 보도자료 11:45 KST입니다. 보도자료 작업과 백업 시작 감시는 Telegram을 발송하지 않습니다. 수동 복구 시 `scheduled_run=true`로 같은 날 정기 슬롯을 사용하고, 웹만 복구하려면 `no_telegram=true`도 선택합니다. Playwright Chromium과 한글 폰트는 Actions 런타임에서 설치합니다.

`AUTO_APPROVAL_ENABLED`, `TELEGRAM_ENABLED`, `PUBLIC_WEB_URL`, `PRESS_RETRY_DELAY_SECONDS`는 GitHub Actions repository variable로 설정합니다. `PRESS_RETRY_DELAY_SECONDS`는 최초 수집에 실패한 활성 `PRESS_RELEASE` 출처만 다시 수집하기 전의 대기 시간이며 기본값은 60초입니다. `FEED_REVALIDATION_SECRET`은 Vercel과 GitHub Actions에 같은 값으로 secret 등록합니다. Telegram Bot token과 대상 chat ID는 GitHub Actions secret 또는 Collector 런타임에만 저장하며 Vercel의 `NEXT_PUBLIC_*`에 넣지 않습니다. 수동 실행은 정기 실행 슬롯과 분리되어 당일 08:35 KST 실행을 막지 않습니다. 3일 dry-run 후 자동 승인, 비공개 시험 채팅, 실제 채널 순서로 단계적으로 켭니다.

## 배포 순서와 관찰

DB migration과 RLS → Collector fixture/contract → Web build → preview 확인 → Collector live smoke → Production 순서로 진행합니다. 첫 운영에서는 출처별 발견·실패율, 승인 대기량, snapshot 발행 성공, 공식 파일 클릭을 확인합니다. 3개 출처가 안정된 뒤에만 5개 이상으로 확대합니다.
