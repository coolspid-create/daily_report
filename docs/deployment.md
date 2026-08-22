# 배포 가이드

## Supabase

1. 별도 프로젝트를 만들고 `supabase/migrations`와 `supabase/seed.sql`을 적용합니다.
2. `supabase test db`로 익명/관리자 RLS를 검증합니다.
3. 관리자 사용자의 `app_metadata.role`을 `admin`으로 설정하고 `ADMIN_ALLOWED_EMAILS`도 방어적으로 구성합니다.
4. 공개 앱에는 anon key만, 웹 서버와 Collector에는 service role/DB 접속값만 둡니다.
5. Storage bucket은 digest 공개 정책과 임시/미러 원본의 비공개 정책을 분리합니다.

## Vercel Web

Vercel Project Root Directory를 `apps/web`으로 지정합니다. `next.config.ts`의 `output: "standalone"`은 Docker 전용이므로 Vercel 배포에서는 사용하지 않습니다. `NEXT_PUBLIC_*`만 브라우저 공개 값으로 넣고 service role은 서버 환경에만 둡니다. 배포 후 `/`, `/admin/login`, `/api/health`, 외부 링크 속성을 확인합니다.

`apps/web/vercel.json`은 매일 23:35 UTC(08:35 KST)에 `/api/cron/daily-publish`를 호출합니다. Vercel에는 `CRON_SECRET`, `GITHUB_ACTIONS_DISPATCH_TOKEN`, `GITHUB_REPOSITORY=coolspid-create/daily_report`, `PUBLIC_FEED_REVALIDATION_SECRET`를 설정합니다. dispatch token은 해당 저장소의 Actions workflow 실행 권한만 갖는 fine-grained token으로 제한합니다.

## Collector

Collector는 Vercel 함수에 직접 넣지 않습니다. Vercel Cron이 GitHub Actions의 `collector.yml`을 정기 실행 입력과 함께 dispatch하고, Actions 러너가 `python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168 --scheduled-run`를 실행합니다. GitHub Actions 화면에서 시작한 수동 실행은 이 입력이 기본적으로 꺼져 있어 별도 실행 키를 사용합니다. Playwright Chromium과 한글 폰트는 Actions 런타임에서 설치합니다. 중복 실행을 막기 위해 `collector.yml`에는 자체 schedule을 두지 않습니다.

`AUTO_APPROVAL_ENABLED`, `TELEGRAM_ENABLED`, `PUBLIC_WEB_URL`은 GitHub Actions repository variable로 설정합니다. `PUBLIC_FEED_REVALIDATION_SECRET`은 Vercel과 GitHub Actions에 같은 값으로 secret 등록합니다. Telegram Bot token과 대상 chat ID는 GitHub Actions secret 또는 Collector 런타임에만 저장하며 Vercel의 `NEXT_PUBLIC_*`에 넣지 않습니다. 수동 실행은 정기 실행 슬롯과 분리되어 당일 08:35 KST 실행을 막지 않습니다. 3일 dry-run 후 자동 승인, 비공개 시험 채팅, 실제 채널 순서로 단계적으로 켭니다.

## 배포 순서와 관찰

DB migration과 RLS → Collector fixture/contract → Web build → preview 확인 → Collector live smoke → Production 순서로 진행합니다. 첫 운영에서는 출처별 발견·실패율, 승인 대기량, snapshot 발행 성공, 공식 파일 클릭을 확인합니다. 3개 출처가 안정된 뒤에만 5개 이상으로 확대합니다.
