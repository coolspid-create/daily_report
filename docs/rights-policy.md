# 권리와 전달 정책

## 기본 원칙

권리 확인 전 원본은 영구 저장하지 않습니다. 기본 권리 상태는 `LINK_ONLY`이며 공식 파일 URL 또는 공식 상세 페이지를 우선합니다. 수집 파일은 분석 목적의 임시 사본이고 기본 TTL은 48시간입니다. 전체 추출 텍스트도 `full_text_retained_until` 이후 제거 대상입니다.

| rights status | 의미 | 허용 delivery mode |
|---|---|---|
| `FILE_UPLOAD_ALLOWED` | 명시적으로 재배포 가능 | `MIRRORED_ALLOWED`, 공식 링크 모드 |
| `LINK_ONLY` | 링크만 제공 | `DIRECT_OFFICIAL_FILE`, `OFFICIAL_PAGE_ONLY` |
| `MANUAL_REVIEW` | 사람이 권리를 확인해야 함 | `SUMMARY_ONLY`, 검토 중 차단 |
| `BLOCKED` | 수집·전달 금지 | `BLOCKED` |

| delivery mode | 공개 버튼 |
|---|---|
| `DIRECT_OFFICIAL_FILE` | 공식 파일 받기 + 공식 출처 |
| `OFFICIAL_PAGE_ONLY` | 공식 페이지에서 받기 |
| `MIRRORED_ALLOWED` | 자체 허용 파일 받기 + 공식 출처 |
| `SUMMARY_ONLY` | 공식 출처만 제공하고 파일 없음 표시 |
| `BLOCKED` | 공개 스냅샷에서 제외 |

세션 의존, 만료형, 서명형 다운로드 URL은 `OFFICIAL_PAGE_ONLY`로 내립니다. 출처에 라이선스가 보이지 않는다는 이유만으로 업로드 허용으로 추정하지 않습니다. 원본 PDF끼리 합치지 않으며 정리본 PDF에는 요약과 공식 링크만 넣습니다.
