# 운영 절차

## 수집 실패

`source_runs`의 상태, 오류 코드, 마지막 cursor를 확인합니다. 일시 오류는 설정된 재시도와 지수 지연 이후 실패로 남기며 cursor는 성공한 신규 항목을 기준으로만 전진합니다. 구조 변경이면 live 페이지를 직접 확인하고 fixture를 새로 고친 뒤 parser 회귀 테스트를 먼저 통과시킵니다. 접근 제한을 우회하지 않습니다.

연속 실패 시 출처는 `DEGRADED`를 거쳐 `DISABLED`가 됩니다. 자동 중지된 활성 출처는 일반 수집 대상에서 제외하고, 리포트와 보도자료 각각의 수집에서 한국 날짜 기준 하루 한 번 복구 점검합니다. 관리자가 비활성화한 출처는 제외합니다. 공식 사이트가 시스템 점검 안내를 반환하면 `SOURCE_MAINTENANCE`로 기록하며 실패 횟수는 증가시키지 않습니다. 오류 없이 신규 후보가 없는 경우는 `HEALTHY`와 빈 수집 횟수로 표시하고, 후보가 있는데 저장하지 못한 경우는 별도 경고를 유지합니다. 공개 화면은 기존 current snapshot을 계속 사용하므로 수집 장애가 즉시 빈 피드가 되지 않습니다.

보도자료 수집은 일부라도 실패하면 성공 자료의 공개 처리를 마친 후 비정상 종료하여 백업 감시에 실제 실패를 전달합니다. 확인한 출처가 하나도 없어도 성공으로 처리하지 않습니다. 백업은 `Collector / press-fallback` 이름으로 한국 날짜 기준 하루 한 번만 시도합니다. `Collector network check` 수동 작업은 DB·발송 없이 공식 목록 주소의 응답과 소요 시간을 확인합니다. HTTP 응답 성공은 목록 파싱 성공을 뜻하지 않습니다.

## 링크 실패

공식 파일이 404, HTML 위장, 만료형이면 `DIRECT_OFFICIAL_FILE`을 유지하지 않습니다. 공식 상세가 정상이라면 `OFFICIAL_PAGE_ONLY`, 둘 다 불가하면 `SUMMARY_ONLY` 또는 `BLOCKED`로 전환하고 검수 기록에 이유를 남깁니다.

## Snapshot 실패와 rollback

새 snapshot은 schema 검증 후 staging되고 마지막에 `activate_snapshot`이 한 트랜잭션으로 current 포인터를 교체합니다. 생성·검증·활성화 중 하나라도 실패하면 새 항목을 current로 만들지 않으므로 직전 정상 버전이 유지됩니다. 복구 시 실패 원인을 수정한 뒤 같은 날짜/range를 재생성하며 기존 current 행을 직접 삭제하지 않습니다.

## 임시 파일 정리

```bash
python -m report_collector cleanup --expired-files
```

기본 TTL은 48시간이며 `.env`의 `TEMP_FILE_TTL_HOURS`로 24~72시간 범위에서 조정합니다. cleanup 전후 삭제 수와 실패 경로를 운영 로그에 남깁니다. 영구 보관이 허용된 `MIRRORED_ALLOWED` 파일과 digest는 임시 정리 대상과 분리합니다.

## 일일 자동 발행

Vercel Cron이 GitHub Actions의 리포트 작업을 월요일부터 금요일 08:35 KST에, 보도자료 작업을 10:30 KST에 호출합니다. 보도자료는 `PRESS_RELEASE` 출처만 수집하고, 실패 출처만 지연 재시도한 뒤 Telegram 없이 공개 스냅샷을 갱신합니다. `press-collection-watchdog.yml`은 평일 11:45 KST로 예약되어 있으며 실행이 지연되어도 당일 10:30 KST 이후의 `main` 브랜치 `Collector / press` 실행 전체를 확인합니다. 대기·실행 중이거나 성공한 작업이 있으면 백업과 알림을 생략하고, 누락 또는 실패한 경우에만 백업 실행과 실제 시각을 포함한 Telegram 알림을 수행합니다. 구버전의 작업 종류가 없는 `Collector` 기록이 당일 존재하면 오탐 방지를 위해 백업을 보류합니다. 감시 작업과 API 모두 주말 실행을 생략합니다. 출처별 timeout은 다음 출처 진행을 막지 않으며 일부 실패는 `PARTIAL`로 기록됩니다.

자동 품질 정책을 모두 통과한 문서만 시스템이 승인합니다. 조건이 불확실하면 `AUTO_HOLD` 감사 기록과 사유 코드를 남기고 관리자 예외 검수함으로 보냅니다. 최근 7일 발행일이 확인된 문서만 자동 검수 후보로 삼아 예전 자료의 재수집이 현재 발행 후보로 집계되지 않게 합니다. 적격 문서가 없으면 `NO_CONTENT`로 종료하고 current snapshot을 교체하지 않으며, 출처 수집 실패가 함께 있으면 `PARTIAL`로 기록합니다. 정기 실행에서는 수집 후보 수를 포함한 신규 발행 자료 없음 안내를 Telegram으로 보냅니다.

```bash
python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168 --dry-run
```

Telegram 실패는 웹 snapshot을 되돌리지 않습니다. `telegram_deliveries`에서 실패 원인을 확인하고 관리자 화면의 재시도 예약을 사용합니다. 개별 원본 PDF는 발송하지 않으며 HTML 브리핑과 자체 정리본 PDF만 보냅니다.
