# 배포 가이드

## Supabase

1. 별도 프로젝트를 만들고 `supabase/migrations`와 `supabase/seed.sql`을 적용합니다.
2. `supabase test db`로 익명/관리자 RLS를 검증합니다.
3. 관리자 사용자의 `app_metadata.role`을 `admin`으로 설정하고 `ADMIN_ALLOWED_EMAILS`도 방어적으로 구성합니다.
4. 공개 앱에는 anon key만, 웹 서버와 Collector에는 service role/DB 접속값만 둡니다.
5. Storage bucket은 digest 공개 정책과 임시/미러 원본의 비공개 정책을 분리합니다.

## Vercel Web

`apps/web`을 프로젝트 root로 지정하거나 monorepo build command를 `pnpm --filter web build`로 설정합니다. `NEXT_PUBLIC_*`만 브라우저 공개 값으로 넣고 service role은 서버 환경에만 둡니다. 배포 후 `/`, `/admin/login`, `/api/health`, 외부 링크 속성을 확인합니다.

## Collector

Collector는 Vercel 함수에 종속시키지 않습니다. `services/collector/Dockerfile`을 스케줄 가능한 컨테이너 환경에 배포하고 `python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168`를 실행합니다. GitHub Actions 예약은 23:35 UTC(08:35 KST)이며 수동 실행도 같은 명령을 사용합니다. Playwright Chromium과 한글 폰트를 이미지에 포함합니다.

`AUTO_APPROVAL_ENABLED`와 `TELEGRAM_ENABLED`는 처음에는 `false`로 배포합니다. Telegram Bot token과 대상 chat ID는 GitHub Actions secret 또는 Collector 런타임에만 저장하며 Vercel의 `NEXT_PUBLIC_*`에 넣지 않습니다. 3일 dry-run 후 자동 승인, 비공개 시험 채팅, 실제 채널 순서로 단계적으로 켭니다.

## 배포 순서와 관찰

DB migration과 RLS → Collector fixture/contract → Web build → preview 확인 → Collector live smoke → Production 순서로 진행합니다. 첫 운영에서는 출처별 발견·실패율, 승인 대기량, snapshot 발행 성공, 공식 파일 클릭을 확인합니다. 3개 출처가 안정된 뒤에만 5개 이상으로 확대합니다.
