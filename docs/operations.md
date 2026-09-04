# 운영 절차

## 수집 실패

`source_runs`의 상태, 오류 코드, 마지막 cursor를 확인합니다. 일시 오류는 설정된 재시도와 지수 지연 이후 실패로 남기며 cursor는 성공한 신규 항목을 기준으로만 전진합니다. 구조 변경이면 live 페이지를 직접 확인하고 fixture를 새로 고친 뒤 parser 회귀 테스트를 먼저 통과시킵니다. 접근 제한을 우회하지 않습니다.

연속 실패 시 관리 화면에서 출처를 `DEGRADED` 또는 `DISABLED`로 바꿉니다. 공개 화면은 기존 current snapshot을 계속 사용하므로 수집 장애가 즉시 빈 피드가 되지 않습니다.

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

Vercel Cron이 GitHub Actions의 리포트 작업을 월요일부터 금요일 08:35 KST에, 보도자료 작업을 10:30 KST에 호출합니다. 보도자료는 `PRESS_RELEASE` 출처만 수집하고, 실패 출처만 지연 재시도한 뒤 Telegram 없이 공개 스냅샷을 갱신합니다. `press-collection-watchdog.yml`은 11:45 KST에 2시간 내 보도자료 작업의 시작·성공 상태를 확인하며, 누락 또는 실패한 경우에만 백업 실행과 Telegram 장애 복구 알림을 수행합니다. 같은 방어 규칙이 API에도 있어 주말 호출이 들어와도 GitHub Actions dispatch를 생략합니다. 출처별 timeout은 다음 출처 진행을 막지 않으며 일부 실패는 `PARTIAL`로 기록됩니다.

자동 품질 정책을 모두 통과한 문서만 시스템이 승인합니다. 조건이 불확실하면 `AUTO_HOLD` 감사 기록과 사유 코드를 남기고 관리자 예외 검수함으로 보냅니다. 최근 7일 발행일이 확인된 문서만 자동 검수 후보로 삼아 예전 자료의 재수집이 현재 발행 후보로 집계되지 않게 합니다. 적격 문서가 없으면 `NO_CONTENT`로 종료하고 current snapshot을 교체하지 않으며, 출처 수집 실패가 함께 있으면 `PARTIAL`로 기록합니다. 정기 실행에서는 수집 후보 수를 포함한 신규 발행 자료 없음 안내를 Telegram으로 보냅니다.

```bash
python -m report_collector daily-publish --timezone Asia/Seoul --window-hours 168 --dry-run
```

Telegram 실패는 웹 snapshot을 되돌리지 않습니다. `telegram_deliveries`에서 실패 원인을 확인하고 관리자 화면의 재시도 예약을 사용합니다. 개별 원본 PDF는 발송하지 않으며 HTML 브리핑과 자체 정리본 PDF만 보냅니다.
