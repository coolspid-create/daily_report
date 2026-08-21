# DESIGN — 오늘의 공공리포트

> 문서 상태: MVP 구현 기준  
> 대상 문서: `PRD.md`의 기능 요구사항을 실제 코드와 시스템 구조로 옮기기 위한 기술·UX 설계  
> 최우선 제약: **공개 화면 한 장, 외부 콘텐츠 수집 API 금지, 파일 하나에 코드 집중 금지**

---

## 1. 설계 목표

이 설계는 다음 목표를 동시에 만족해야 합니다.

1. 사용자는 첫 화면에서 관심 분야를 한 번 누르고 파일을 받을 수 있어야 합니다.
2. 공개 화면은 가볍고 빠르며, 내부 데이터 구조와 수집 복잡성을 노출하지 않아야 합니다.
3. 기관별 사이트 구조가 달라도 작은 어댑터 단위로 추가·수정할 수 있어야 합니다.
4. 수집, 분석, 검수, 공개를 분리해 한 단계의 장애가 전체 서비스에 영향을 주지 않게 해야 합니다.
5. 페이지·컴포넌트·어댑터 하나에 로직이 몰리지 않도록 모듈 경계를 명확히 해야 합니다.
6. MVP는 작게 시작하되, 출처 20~25곳까지 확장 가능한 구조여야 합니다.

---

## 2. 핵심 설계 원칙

### 2.1 공개 UI 원칙

- 한 페이지, 한 열, 한 가지 핵심 행동
- 분야 변경은 내비게이션이 아니라 상태 전환
- 보고서 상세 페이지 없음
- 표지 이미지·차트·복잡한 필터 없음
- 카드 안에서 판단과 다운로드 완료
- 실시간 AI 호출 없음
- 오늘 데이터는 사전 생성된 스냅샷 사용

### 2.2 시스템 원칙

- 외부 콘텐츠 수집은 공개 HTML·RSS·첨부파일·브라우저 렌더링만 사용
- 문서화되지 않은 JSON·XHR 주소 직접 호출 금지
- 출처별 로직을 독립 어댑터로 분리
- 수집과 공개를 직접 연결하지 않고 관리자 승인과 스냅샷을 사이에 둠
- 원본 파일 저장은 최소화하고 공식 링크 우선
- 모든 실행은 재실행해도 중복되지 않는 idempotent 구조
- 공개 앱은 읽기 전용 스냅샷만 소비

### 2.3 코드 구조 원칙

- `page.tsx`와 Route Handler는 조립만 담당
- 비즈니스 규칙은 feature/service 계층에 위치
- 기관별 parser를 거대 switch 문으로 합치지 않음
- `utils.ts`, `helpers.py` 같은 범용 쓰레기통 파일 금지
- 데이터 접근은 repository 계층으로 제한
- 외부 서비스 호출은 provider/interface 뒤에 숨김
- 테스트 fixture는 실제 사이트 HTML·PDF를 축약한 로컬 파일로 관리

---

## 3. 전체 시스템 구조

```text
┌──────────────────────────────────────────────────────────┐
│                    공개 웹 사용자                        │
│  관심 분야 선택 → 보고서 카드 확인 → 공식 파일 받기      │
└──────────────────────────┬───────────────────────────────┘
                           │ 읽기 전용
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   Next.js Web App                        │
│  Public One-page Feed | Admin Review | Internal Routes   │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                Supabase PostgreSQL/Storage               │
│ 문서 메타 | 출처 | 검수 | 공개 스냅샷 | 정리본 PDF | 로그 │
└──────────────────────────▲───────────────────────────────┘
                           │
                           │ 저장/갱신
┌──────────────────────────┴───────────────────────────────┐
│                   Python Collector                       │
│ Discover → Fetch → Validate → Extract → Deduplicate      │
│ → Classify → Summarize → Rights → Review Queue           │
└──────────────────────────▲───────────────────────────────┘
                           │ 공개 HTML/RSS/첨부/렌더링
                           │ API·숨은 JSON 엔드포인트 금지
┌──────────────────────────┴───────────────────────────────┐
│       정부·국회·공공기관·연구기관 공개 웹사이트          │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 권장 런타임 구성

### 4.1 공개·관리자 웹

- Next.js App Router
- TypeScript strict mode
- React Server Components 우선
- Tailwind CSS 또는 작은 자체 CSS 토큰
- Supabase Auth는 관리자에만 사용
- 공개 피드는 서버에서 스냅샷을 읽어 초기 HTML에 포함
- 분야 전환은 클라이언트에서 이미 받은 스냅샷을 필터링

### 4.2 수집 Worker

- Python 3.12 이상
- `httpx`: 정적 HTML·파일 요청
- `BeautifulSoup` 또는 `selectolax`: HTML 파싱
- `Playwright`: 공개 페이지 렌더링이 필요한 경우만 사용
- `PyMuPDF`: PDF 메타·텍스트·페이지 정보 추출
- `Pydantic`: 데이터 계약 검증
- `SQLAlchemy` 또는 Supabase/PostgREST를 감싼 repository
- `pytest`: fixture 기반 테스트

### 4.3 데이터·저장소

- Supabase PostgreSQL
- Supabase Storage
  - `digests`: 서비스 생성 정리본 PDF
  - `temporary-source-files`: 제한된 수명의 임시 원본
  - `mirrored-source-files`: 재배포 확인 자료만
- Row Level Security
- 공개 피드는 공개 스냅샷 테이블 또는 정적 JSON만 읽기 허용

### 4.4 스케줄·배포

MVP 권장안:

- Web: Vercel
- DB/Auth/Storage: Supabase
- Collector: Docker 기반 실행
- 스케줄: GitHub Actions cron 또는 별도 경량 컨테이너 스케줄러
- 장시간 작업은 Vercel Function 안에서 수행하지 않음

구현은 스케줄러에 종속되지 않도록 CLI 명령으로 시작할 수 있어야 합니다.

```bash
python -m report_collector collect --source=nkis
python -m report_collector collect --all-active
python -m report_collector build-snapshot --date=2026-08-21
python -m report_collector build-digest --date=2026-08-21 --topic=ai-tech
```

---

## 5. 공개 UX 설계

### 5.1 데스크톱 와이어프레임

```text
┌─────────────────────────────────────────────────────────────┐
│ 오늘의 공공리포트                      08.21 08:30 업데이트 │
│ 정부·공공기관의 오늘 읽을 보고서만 정리합니다.             │
├─────────────────────────────────────────────────────────────┤
│ [전체] [경제·금융] [산업·통상] [AI·과학기술]               │
│ [노동·복지] [교육·인구] [국토·환경] [법·외교·안보]         │
│                                                [오늘|7일]    │
├─────────────────────────────────────────────────────────────┤
│ AI·과학기술 · 오늘 선정 6건       [오늘 정리본 PDF 받기]   │
├─────────────────────────────────────────────────────────────┤
│ [정책 변화] [NEW]                                          │
│ AI 기본의료 전략                                           │
│ 관계부처 합동 · 2026.08.21 · PDF · 74쪽 · 3.2MB            │
│                                                             │
│ 왜 볼 만한가                                                │
│ 지역·필수의료에 AI를 적용하는 정부 방향을 구체화했습니다.  │
│                                                             │
│ · 생활 속 AI 의료서비스 확대                               │
│ · 지역 의료기관의 디지털 기반 구축                         │
│ · 의료 AI 산업 생태계와 규제 정비                          │
│                                     [PDF 받기] [공식 출처]  │
├─────────────────────────────────────────────────────────────┤
│ 보고서 카드 2                                               │
├─────────────────────────────────────────────────────────────┤
│ 보고서 카드 3                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 모바일 와이어프레임

```text
┌─────────────────────────────┐
│ 오늘의 공공리포트           │
│ 08.21 08:30 업데이트        │
├─────────────────────────────┤
│ [전체][경제][산업][AI] →    │
│ [노동][교육][환경][법·안보] │
├─────────────────────────────┤
│ AI·과학기술 · 6건           │
│ [오늘] [최근 7일]           │
│ [정리본 PDF 받기]           │
├─────────────────────────────┤
│ [NEW] [정책 변화]           │
│ AI 기본의료 전략            │
│ 관계부처 합동               │
│ 2026.08.21 · PDF · 74쪽     │
│                             │
│ 왜 볼 만한가                │
│ 지역·필수의료 AI 방향을     │
│ 구체화한 정부 전략입니다.   │
│                             │
│ · 핵심 1                    │
│ · 핵심 2                    │
│ · 핵심 3                    │
│                             │
│ [PDF 받기]                  │
│ [공식 출처]                 │
└─────────────────────────────┘
```

### 5.3 상호작용 규칙

- 분야 버튼은 `button` 요소로 구현합니다.
- 현재 선택 분야는 `aria-pressed="true"`를 사용합니다.
- 클릭 즉시 현재 메모리의 피드를 필터링합니다.
- URL은 `history.replaceState` 또는 Next Router의 shallow 성격으로 갱신합니다.
- 마지막 선택 분야는 `localStorage`에 저장합니다.
- 저장값이 유효하지 않으면 `all`로 복귀합니다.
- 분야 변경 시 스크롤을 맨 위로 강제로 이동시키지 않습니다.
- 기간을 바꿀 때만 필요한 데이터를 추가 로드할 수 있습니다.

### 5.4 시각 토큰

복잡한 분야별 컬러 체계를 사용하지 않습니다.

```css
:root {
  --color-bg: #f7f8fa;
  --color-surface: #ffffff;
  --color-text: #17191c;
  --color-muted: #667085;
  --color-border: #e5e7eb;
  --color-accent: #2563eb;
  --color-accent-soft: #eff6ff;
  --color-danger: #b42318;
  --radius-card: 16px;
  --radius-control: 999px;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.06);
  --content-width: 960px;
}
```

실제 구현에서는 디자인 토큰을 별도 파일로 관리하고 컴포넌트 안에 색상 값을 반복해서 작성하지 않습니다.

---

## 6. 관리자 UX 설계

### 6.1 관리자 경로

```text
/admin
```

관리자도 깊은 페이지 구조를 피합니다. MVP는 상단의 2개 전환만 허용합니다.

- 검수 대기
- 출처 상태

### 6.2 검수 화면

```text
┌──────────────────────────────────────────────────────────────┐
│ 관리자 · 검수 대기 18건                    [출처 상태]       │
├──────────────────────────────┬───────────────────────────────┤
│ 문서 목록                    │ 선택 문서 인라인 작업 패널    │
│                              │                               │
│ [NEW] 보고서 A               │ 제목                          │
│ 기관 · 날짜 · 파일           │ [_________________________]   │
│ AI·과학기술 91%              │ 대표 분야 [AI·과학기술 ▼]     │
│ 중복 후보 1건                │ 왜 볼 만한가                  │
│                              │ [_________________________]   │
│ [NEW] 보고서 B               │ 핵심 1/2/3                    │
│ ...                          │ 파일 모드 [공식 PDF ▼]        │
│                              │ [제외] [보류] [승인]          │
└──────────────────────────────┴───────────────────────────────┘
```

모바일 관리자 화면은 우선순위가 낮지만, 목록 선택 후 작업 패널을 같은 페이지의 아래쪽에 펼치는 방식으로 대응합니다.

### 6.3 관리자 디자인 원칙

- 검수는 한 문서당 60초 안에 끝나야 합니다.
- 상세 정보를 여러 페이지로 분리하지 않습니다.
- AI 근거 페이지와 중복 후보는 접을 수 있는 보조 영역에 둡니다.
- 승인·제외 버튼은 항상 작업 패널 하단에 고정합니다.
- 출처 상태 화면은 차트 없이 표와 상태 배지만 사용합니다.

---

## 7. 라우트 설계

### 7.1 공개 라우트

| 경로 | 역할 |
|---|---|
| `/` | 공개 한 페이지 피드 |
| `/robots.txt` | 검색엔진 정책 |
| `/sitemap.xml` | 필요 시 공개 날짜 스냅샷만 포함 |

보고서별 내부 상세 경로는 만들지 않습니다.

### 7.2 관리자 라우트

| 경로 | 역할 |
|---|---|
| `/admin` | 검수 대기 기본 화면 |
| `/admin/login` | 관리자 로그인 |

`/admin/sources`, `/admin/documents/:id`처럼 뎁스를 늘리는 대신 `/admin` 안의 상태 전환과 인라인 패널을 사용합니다. URL이 필요한 경우 검색 매개변수만 사용합니다.

```text
/admin?view=review&document=uuid
/admin?view=sources
```

### 7.3 내부 Route Handler

외부 콘텐츠 수집 API가 아니라 서비스 내부 기능용입니다.

```text
/api/admin/review-items
/api/admin/documents/[id]/approve
/api/admin/documents/[id]/reject
/api/admin/documents/[id]/update
/api/admin/documents/[id]/merge
/api/admin/publications/build
/api/admin/digests/build
/api/health
```

Route Handler는 인증·입력 검증·서비스 호출·응답 변환만 담당합니다.

---

## 8. 프런트엔드 모듈 구조

### 8.1 공개 feature

```text
features/public-feed/
├─ components/
│  ├─ feed-header.tsx
│  ├─ topic-selector.tsx
│  ├─ range-toggle.tsx
│  ├─ digest-download.tsx
│  ├─ report-list.tsx
│  ├─ report-card.tsx
│  ├─ report-meta.tsx
│  ├─ report-actions.tsx
│  ├─ empty-feed.tsx
│  └─ feed-error.tsx
├─ hooks/
│  ├─ use-active-topic.ts
│  └─ use-feed-filter.ts
├─ lib/
│  ├─ filter-feed.ts
│  ├─ topic-storage.ts
│  ├─ build-feed-url.ts
│  └─ report-action-label.ts
├─ server/
│  └─ get-public-snapshot.ts
├─ types/
│  ├─ public-feed.ts
│  └─ public-report.ts
└─ constants/
   └─ topics.ts
```

### 8.2 관리자 feature

```text
features/admin-review/
├─ components/
│  ├─ review-workbench.tsx
│  ├─ review-list.tsx
│  ├─ review-list-item.tsx
│  ├─ review-editor.tsx
│  ├─ summary-fields.tsx
│  ├─ duplicate-panel.tsx
│  ├─ evidence-panel.tsx
│  └─ review-actions.tsx
├─ actions/
│  ├─ approve-document.ts
│  ├─ reject-document.ts
│  ├─ update-document.ts
│  └─ merge-document.ts
├─ server/
│  ├─ get-review-items.ts
│  └─ get-source-health.ts
├─ schemas/
│  └─ review-form.schema.ts
└─ types/
   └─ admin-review.ts
```

### 8.3 컴포넌트 경계

- `page.tsx`는 데이터를 가져와 최상위 feature에 전달만 합니다.
- `report-card.tsx`는 렌더링만 하며 링크 정책을 결정하지 않습니다.
- 링크 정책은 `report-action-label.ts`와 서버에서 만들어진 `delivery` 데이터가 담당합니다.
- 관리자 Server Action 또는 Route Handler는 repository를 직접 호출하지 않고 application service를 호출합니다.

---

## 9. Collector 아키텍처

### 9.1 계층

```text
CLI/Scheduler
    ↓
Application Pipeline
    ↓
Domain Services
    ↓
Adapters / Providers / Repositories
```

### 9.2 어댑터 유형

```text
StaticBoardAdapter
- 서버가 완성된 HTML을 반환하는 일반 게시판

RenderedBoardAdapter
- 공개 페이지가 브라우저 렌더링을 필요로 하는 게시판

RepositoryAdapter
- 공개 리포지터리의 목록·상세·파일 구조

SearchPortalAdapter
- 검색 조건과 페이지 이동이 필요한 공개 포털

RssAdapter
- 기관이 공식 제공하는 RSS·Atom
```

MVP에서는 `StaticBoardAdapter`, `RenderedBoardAdapter`, `RssAdapter`를 우선 구현합니다.

### 9.3 Source Adapter 계약

```python
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

class SourceAdapter(ABC):
    @abstractmethod
    async def discover(self, cursor: str | None) -> AsyncIterator[DiscoveredItem]:
        """공개 목록에서 신규 후보를 반환한다."""

    @abstractmethod
    async def fetch_detail(self, item: DiscoveredItem) -> SourceDocument:
        """공개 상세 페이지와 첨부파일 메타데이터를 해석한다."""

    @abstractmethod
    async def health_check(self) -> SourceHealthResult:
        """목록과 필수 selector가 정상인지 확인한다."""
```

### 9.4 어댑터 구현 규칙

- 한 출처의 파일은 자체 폴더에 둡니다.
- HTML selector와 파싱 규칙을 코드와 분리할 수 있으면 YAML로 분리합니다.
- selector만 다른 단순 출처는 범용 어댑터와 설정 파일로 처리합니다.
- 예외가 많아지면 해당 출처 전용 parser를 추가합니다.
- 모든 출처는 HTML fixture와 최소 1개 상세 fixture를 가져야 합니다.

예시:

```text
sources/
└─ nars/
   ├─ adapter.py
   ├─ parser.py
   ├─ selectors.py
   └─ tests/
      ├─ fixtures/list.html
      ├─ fixtures/detail.html
      └─ test_parser.py
```

---

## 10. 수집 파이프라인 상태 머신

```text
DISCOVERED
    ↓
DETAIL_FETCHED
    ↓
FILE_IDENTIFIED ─────────────→ OFFICIAL_PAGE_ONLY
    ↓
FILE_DOWNLOADED
    ↓
FILE_VALIDATED ──────────────→ FILE_INVALID
    ↓
TEXT_EXTRACTED ──────────────→ OCR_REQUIRED
    ↓
DEDUPLICATED ────────────────→ MERGED
    ↓
CLASSIFIED
    ↓
SUMMARIZED ──────────────────→ SUMMARY_FAILED
    ↓
RIGHTS_EVALUATED
    ↓
NEEDS_REVIEW
    ↓
APPROVED / REJECTED
    ↓
PUBLISHED
```

각 단계는 독립적으로 재실행할 수 있어야 하며, 완료된 단계를 중복 수행하지 않도록 상태와 버전을 저장합니다.

---

## 11. 파이프라인 모듈 분리

```text
pipelines/
├─ collect_source.py
├─ process_document.py
├─ publish_snapshot.py
└─ build_digest.py

services/
├─ discovery_service.py
├─ file_validation_service.py
├─ deduplication_service.py
├─ classification_service.py
├─ summarization_service.py
├─ rights_service.py
├─ ranking_service.py
└─ publication_service.py

extractors/
├─ pdf_metadata_extractor.py
├─ pdf_text_extractor.py
├─ publication_date_extractor.py
└─ license_extractor.py

providers/
├─ ai/
│  ├─ base.py
│  ├─ mock_provider.py
│  └─ configured_provider.py
├─ browser/
│  ├─ base.py
│  └─ playwright_browser.py
└─ storage/
   ├─ base.py
   └─ supabase_storage.py
```

파이프라인은 순서를 조율하고, 실제 규칙은 service에 둡니다.

---

## 12. 데이터 모델

### 12.1 핵심 ERD

```text
sources 1 ─── N source_runs
sources 1 ─── N source_items
source_items N ─── 1 documents

documents 1 ─── N document_sources
documents 1 ─── N document_files
documents 1 ─── 1 document_analysis
documents N ─── N topics (document_topics)
documents 1 ─── N review_actions

daily_publications 1 ─── N publication_items
publication_items N ─── 1 documents

daily_publications 1 ─── N digest_files
feed_snapshots N ─── 1 daily_publications
```

### 12.2 테이블 개요

#### `sources`

```text
id uuid pk
slug text unique
name text
source_kind text
list_url text
homepage_url text
adapter_key text
config_path text
rights_default text
poll_interval_minutes int
request_delay_ms int
active boolean
status text
last_success_at timestamptz
consecutive_failures int
created_at timestamptz
updated_at timestamptz
```

#### `source_runs`

```text
id uuid pk
source_id uuid fk
started_at timestamptz
finished_at timestamptz
status text
discovered_count int
new_count int
updated_count int
failed_count int
cursor_before text
cursor_after text
error_code text
error_message text
```

#### `source_items`

```text
id uuid pk
source_id uuid fk
source_item_key text
list_title text
list_published_at timestamptz
detail_url text
first_seen_at timestamptz
last_seen_at timestamptz
document_id uuid nullable fk
raw_metadata jsonb
unique(source_id, source_item_key)
```

#### `documents`

```text
id uuid pk
canonical_title text
normalized_title text
institution text
published_at date
summary_status text
workflow_status text
primary_topic_id text
content_tag text
why_it_matters text
rights_status text
delivery_mode text
primary_source_url text
created_at timestamptz
updated_at timestamptz
```

#### `document_sources`

```text
id uuid pk
document_id uuid fk
source_id uuid fk
source_item_id uuid fk
detail_url text
is_original_publisher boolean
priority int
unique(document_id, source_item_id)
```

#### `document_files`

```text
id uuid pk
document_id uuid fk
source_item_id uuid fk
file_url text
file_name text
mime_type text
extension text
size_bytes bigint
page_count int
sha256 text
is_encrypted boolean
validation_status text
storage_path text nullable
expires_at timestamptz nullable
created_at timestamptz
```

#### `document_analysis`

```text
document_id uuid pk fk
why_it_matters text
key_points jsonb
secondary_topic_ids jsonb
content_tag text
confidence numeric
evidence_pages jsonb
analysis_version text
provider_key text
full_text_retained_until timestamptz nullable
created_at timestamptz
updated_at timestamptz
```

#### `topics`

```text
id text pk
label text
sort_order int
active boolean
```

#### `document_topics`

```text
document_id uuid fk
topic_id text fk
score numeric
is_primary boolean
primary key(document_id, topic_id)
```

#### `review_actions`

```text
id uuid pk
document_id uuid fk
actor_id uuid fk
action text
before_data jsonb
after_data jsonb
reason text
created_at timestamptz
```

#### `daily_publications`

```text
id uuid pk
publication_date date
range_key text
status text
published_at timestamptz
snapshot_version int
unique(publication_date, range_key)
```

#### `publication_items`

```text
id uuid pk
publication_id uuid fk
document_id uuid fk
topic_id text
rank int
is_featured boolean
unique(publication_id, document_id, topic_id)
```

#### `feed_snapshots`

```text
id uuid pk
publication_id uuid fk
range_key text
snapshot_json jsonb
checksum text
created_at timestamptz
is_current boolean
```

#### `digest_files`

```text
id uuid pk
publication_id uuid fk
topic_id text
storage_path text
file_size_bytes bigint
checksum text
generated_at timestamptz
status text
```

---

## 13. 공개 피드 스냅샷 계약

공개 웹은 여러 테이블을 조합하지 않고 아래 형태의 스냅샷 하나를 읽습니다.

```json
{
  "version": 1,
  "generatedAt": "2026-08-21T08:30:00+09:00",
  "range": "today",
  "topics": [
    {"id": "all", "label": "전체", "count": 12},
    {"id": "ai-tech", "label": "AI·과학기술", "count": 6}
  ],
  "reportsByTopic": {
    "ai-tech": [
      {
        "id": "uuid",
        "title": "AI 기본의료 전략",
        "institution": "관계부처 합동",
        "publishedAt": "2026-08-21",
        "contentTag": "정책 변화",
        "isNew": true,
        "whyItMatters": "지역·필수의료에 AI를 적용하는 정부 방향을 구체화했습니다.",
        "keyPoints": ["핵심 1", "핵심 2", "핵심 3"],
        "file": {
          "format": "PDF",
          "sizeBytes": 3355443,
          "pageCount": 74,
          "deliveryMode": "DIRECT_OFFICIAL_FILE",
          "downloadUrl": "https://official.example/report.pdf",
          "sourceUrl": "https://official.example/report"
        }
      }
    ]
  },
  "digests": {
    "ai-tech": {
      "available": true,
      "url": "https://storage.example/digests/2026-08-21-ai-tech.pdf"
    }
  }
}
```

### 13.1 스냅샷 규칙

- 공개에 필요한 필드만 포함합니다.
- 관리자 메모, AI 모델명, 내부 점수, 권리 검토 상세는 포함하지 않습니다.
- URL은 서버에서 전달 모드 검증 후 넣습니다.
- 오늘 모든 분야의 카드가 60건 이하이면 한 번에 전달합니다.
- 최근 7일 스냅샷은 별도 요청으로 지연 로드할 수 있습니다.
- 새 스냅샷 생성 실패 시 `is_current=true`인 직전 버전을 유지합니다.

---

## 14. 중복 제거 설계

### 14.1 단계별 판정

1. 동일 `source_id + source_item_key` → 같은 수집항목
2. 동일 정규화 상세 URL → 같은 출처 항목
3. 동일 파일 SHA-256 → 같은 문서 확정
4. 동일 정규화 제목 + 발행일 + 기관 → 높은 중복 가능성
5. 제목 유사도 임계값 초과 → 관리자 중복 후보

### 14.2 제목 정규화

- 양쪽 공백 제거
- 연속 공백 축소
- 파일 확장자 제거
- 목록 번호·대괄호 기관표기 등 반복 접두어 제거
- 유니코드 정규화
- 기호의 표준화
- 연도·회차는 무조건 제거하지 않음

### 14.3 병합 정책

- 원 발행기관 출처를 `primary_source_url`로 선택합니다.
- 통합 포털 링크는 보조 출처로 보존합니다.
- 더 신뢰할 수 있는 파일 메타데이터가 있으면 대표 파일을 갱신합니다.
- 제목 또는 내용이 개정되었고 파일 해시가 다르면 버전 관계로 처리할 수 있도록 여지를 둡니다.

---

## 15. 파일 전달·권리 설계

### 15.1 전달 결정 함수

```text
권리 상태가 BLOCKED인가?
  → 공개 제외

공식 파일 URL이 안정적이고 공개 접근 가능한가?
  → DIRECT_OFFICIAL_FILE

파일 URL이 세션 의존·만료형인가?
  → OFFICIAL_PAGE_ONLY

재배포 허용이 명확하고 저장 파일이 존재하는가?
  → MIRRORED_ALLOWED

원문 접근이 없지만 공개 가능한 메타·요약이 있는가?
  → SUMMARY_ONLY
```

### 15.2 URL 점검

- 게시 전에 HEAD 또는 제한적 GET으로 응답을 확인합니다.
- HEAD를 지원하지 않는 사이트는 작은 범위의 GET 또는 브라우저 검증을 사용합니다.
- 로그인 페이지, HTML 오류 페이지, 빈 파일을 PDF로 오판하지 않습니다.
- 링크 실패가 반복되면 `OFFICIAL_PAGE_ONLY`로 전환하고 관리자에게 표시합니다.

### 15.3 임시 파일 수명

```text
temporary-source-files/
└─ 기본 TTL 24~72시간

mirrored-source-files/
└─ FILE_UPLOAD_ALLOWED 자료만 영구 또는 정책 기간 보관
```

삭제 작업은 별도 cleanup 명령으로 수행합니다.

```bash
python -m report_collector cleanup --expired-files
```

---

## 16. AI 분석 설계

### 16.1 provider 인터페이스

특정 모델 SDK를 도메인 로직에 직접 사용하지 않습니다.

```python
class AnalysisProvider(Protocol):
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        ...
```

### 16.2 입력 전략

- 표지·발행정보
- 요약·초록
- 목차
- 주요 결과
- 결론·정책 제언
- 필요한 경우 제한된 추가 청크

PDF 전체를 무조건 한 번에 전달하지 않습니다.

### 16.3 출력 검증

- Pydantic 스키마로 검증합니다.
- `key_points`는 1~3개로 제한합니다.
- `why_it_matters` 길이를 제한합니다.
- 허용된 topic 코드와 content tag만 받습니다.
- evidence page가 실제 페이지 범위를 넘지 않는지 검증합니다.
- 실패 시 재시도 후 `SUMMARY_FAILED`로 전환합니다.

### 16.4 버전 관리

- `analysis_version`
- `prompt_version`
- `provider_key`
- `extractor_version`

동일 문서를 재분석할 때 이전 결과와 구분할 수 있어야 합니다.

---

## 17. 정리본 PDF 생성 설계

### 17.1 생성 방식

- 승인된 스냅샷으로 HTML 템플릿 생성
- Playwright의 print-to-PDF 또는 동등한 서버 렌더링 사용
- Collector에 이미 Playwright가 있으므로 중복 도구 도입을 피함

### 17.2 PDF 구성

1. 날짜·분야·업데이트 시각
2. 오늘 선정 건수
3. 보고서별 제목·기관·발행일
4. 왜 볼 만한가
5. 핵심 내용 3개
6. 공식 출처 및 파일 링크
7. 출처·이용 안내

### 17.3 생성 모듈

```text
digest/
├─ digest_builder.py
├─ digest_view_model.py
├─ digest_renderer.py
├─ digest_storage.py
└─ templates/
   ├─ digest.html.j2
   └─ digest.css
```

템플릿, 데이터 조립, PDF 렌더링, 저장을 한 파일에 넣지 않습니다.

---

## 18. 저장소 구조

```text
public-report-service/
├─ PRD.md
├─ DESIGN.md
├─ CODEX_PROMPT.md
├─ README.md
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
├─ pnpm-workspace.yaml
├─ package.json
├─ pyproject.toml
│
├─ apps/
│  └─ web/
│     ├─ app/
│     │  ├─ (public)/
│     │  │  └─ page.tsx
│     │  ├─ admin/
│     │  │  ├─ login/
│     │  │  │  └─ page.tsx
│     │  │  └─ page.tsx
│     │  ├─ api/
│     │  │  ├─ admin/
│     │  │  │  ├─ documents/
│     │  │  │  │  └─ [id]/
│     │  │  │  │     ├─ approve/route.ts
│     │  │  │  │     ├─ reject/route.ts
│     │  │  │  │     ├─ update/route.ts
│     │  │  │  │     └─ merge/route.ts
│     │  │  │  ├─ publications/
│     │  │  │  │  └─ build/route.ts
│     │  │  │  └─ digests/
│     │  │  │     └─ build/route.ts
│     │  │  └─ health/route.ts
│     │  ├─ layout.tsx
│     │  ├─ globals.css
│     │  ├─ robots.ts
│     │  └─ sitemap.ts
│     │
│     ├─ features/
│     │  ├─ public-feed/
│     │  │  ├─ components/
│     │  │  ├─ hooks/
│     │  │  ├─ lib/
│     │  │  ├─ server/
│     │  │  ├─ constants/
│     │  │  └─ types/
│     │  ├─ admin-review/
│     │  │  ├─ components/
│     │  │  ├─ actions/
│     │  │  ├─ schemas/
│     │  │  ├─ server/
│     │  │  └─ types/
│     │  └─ source-health/
│     │     ├─ components/
│     │     ├─ server/
│     │     └─ types/
│     │
│     ├─ components/
│     │  ├─ ui/
│     │  └─ layout/
│     ├─ lib/
│     │  ├─ auth/
│     │  ├─ database/
│     │  ├─ http/
│     │  ├─ formatting/
│     │  └─ validation/
│     ├─ styles/
│     │  └─ tokens.css
│     ├─ tests/
│     │  ├─ unit/
│     │  ├─ integration/
│     │  └─ e2e/
│     ├─ next.config.ts
│     ├─ tsconfig.json
│     └─ package.json
│
├─ services/
│  └─ collector/
│     ├─ src/
│     │  └─ report_collector/
│     │     ├─ cli/
│     │     │  ├─ main.py
│     │     │  ├─ collect_command.py
│     │     │  ├─ snapshot_command.py
│     │     │  ├─ digest_command.py
│     │     │  └─ cleanup_command.py
│     │     ├─ domain/
│     │     │  ├─ models.py
│     │     │  ├─ enums.py
│     │     │  ├─ errors.py
│     │     │  └─ policies.py
│     │     ├─ adapters/
│     │     │  ├─ base.py
│     │     │  ├─ generic/
│     │     │  │  ├─ static_board.py
│     │     │  │  ├─ rendered_board.py
│     │     │  │  ├─ rss_feed.py
│     │     │  │  └─ repository.py
│     │     │  └─ sources/
│     │     │     ├─ sample_static/
│     │     │     ├─ sample_rendered/
│     │     │     └─ nars/
│     │     ├─ pipelines/
│     │     │  ├─ collect_source.py
│     │     │  ├─ process_document.py
│     │     │  ├─ publish_snapshot.py
│     │     │  └─ build_digest.py
│     │     ├─ services/
│     │     │  ├─ discovery_service.py
│     │     │  ├─ file_validation_service.py
│     │     │  ├─ deduplication_service.py
│     │     │  ├─ classification_service.py
│     │     │  ├─ summarization_service.py
│     │     │  ├─ rights_service.py
│     │     │  ├─ ranking_service.py
│     │     │  └─ publication_service.py
│     │     ├─ extractors/
│     │     │  ├─ pdf_metadata_extractor.py
│     │     │  ├─ pdf_text_extractor.py
│     │     │  ├─ publication_date_extractor.py
│     │     │  └─ license_extractor.py
│     │     ├─ providers/
│     │     │  ├─ ai/
│     │     │  ├─ browser/
│     │     │  ├─ storage/
│     │     │  └─ http/
│     │     ├─ repositories/
│     │     │  ├─ source_repository.py
│     │     │  ├─ document_repository.py
│     │     │  ├─ publication_repository.py
│     │     │  └─ supabase/
│     │     ├─ digest/
│     │     │  ├─ digest_builder.py
│     │     │  ├─ digest_view_model.py
│     │     │  ├─ digest_renderer.py
│     │     │  ├─ digest_storage.py
│     │     │  └─ templates/
│     │     ├─ config/
│     │     │  ├─ settings.py
│     │     │  └─ logging.py
│     │     └─ observability/
│     │        ├─ metrics.py
│     │        └─ run_logger.py
│     ├─ tests/
│     │  ├─ unit/
│     │  ├─ integration/
│     │  ├─ contracts/
│     │  └─ fixtures/
│     │     ├─ html/
│     │     ├─ pdf/
│     │     └─ snapshots/
│     ├─ Dockerfile
│     └─ pyproject.toml
│
├─ contracts/
│  ├─ public-feed.schema.json
│  ├─ analysis-result.schema.json
│  ├─ source-config.schema.json
│  └─ generated/
│     ├─ typescript/
│     └─ python/
│
├─ config/
│  └─ sources/
│     ├─ registry.yaml
│     ├─ sample-static.yaml
│     ├─ sample-rendered.yaml
│     └─ nars.yaml
│
├─ supabase/
│  ├─ migrations/
│  │  ├─ 0001_core_sources.sql
│  │  ├─ 0002_documents_and_files.sql
│  │  ├─ 0003_analysis_and_topics.sql
│  │  ├─ 0004_review_and_publication.sql
│  │  └─ 0005_rls_and_policies.sql
│  ├─ seed.sql
│  └─ tests/
│     └─ rls.sql
│
├─ scripts/
│  ├─ generate-contract-types.sh
│  ├─ verify-file-sizes.py
│  ├─ check-source-configs.py
│  └─ smoke-test.sh
│
├─ docs/
│  ├─ operations.md
│  ├─ source-adapter-guide.md
│  ├─ rights-policy.md
│  └─ deployment.md
│
└─ .github/
   └─ workflows/
      ├─ ci.yml
      ├─ collector-schedule.yml
      └─ source-smoke.yml
```

---

## 19. 파일·코드 크기 제한

### 19.1 권장 기준

| 대상 | 권장 | 검토 필요 | 원칙상 금지 |
|---|---:|---:|---:|
| TypeScript/TSX 파일 | 250줄 이하 | 251~350줄 | 350줄 초과 |
| Python 파일 | 250줄 이하 | 251~350줄 | 350줄 초과 |
| React 컴포넌트 | 150줄 이하 | 151~220줄 | 220줄 초과 |
| 함수 | 40줄 이하 | 41~70줄 | 70줄 초과 |
| Route Handler | 80줄 이하 | 81~120줄 | 비즈니스 로직 포함 |
| 테스트 파일 | 300줄 이하 | 301~450줄 | 여러 기능군 혼합 |

기계 생성 파일, SQL migration, schema는 예외가 될 수 있지만 사람이 작성하는 로직 파일은 위 기준을 적용합니다.

### 19.2 분리 신호

다음 중 하나라도 해당하면 파일을 분리합니다.

- 서로 다른 도메인 명사를 처리함
- 외부 요청과 파싱과 저장을 한 함수에서 수행함
- 3개 이상의 UI 상태를 한 컴포넌트가 직접 관리함
- 조건문이 출처별로 계속 추가됨
- 테스트가 하나의 파일에서 3개 이상의 기능군을 다룸
- 파일명이 `utils`, `common`, `misc`, `helpers`이고 내용이 계속 늘어남

### 19.3 자동 검사

`scripts/verify-file-sizes.py`를 CI에서 실행하여 임계치를 넘는 파일을 실패 처리하거나 경고합니다.

예외가 필요하면 파일 상단 주석이 아니라 별도 allowlist에 사유와 만료일을 기록합니다.

---

## 20. Source 설정 구조

단순 게시판은 코드 대신 출처별 YAML 설정을 사용합니다.

```yaml
id: nars
name: 국회입법조사처
adapter: static_board
homepage_url: https://example.go.kr
list_url: https://example.go.kr/reports
rights_default: LINK_ONLY
poll_interval_minutes: 720
request_delay_ms: 1200

selectors:
  list_item: "ul.report-list > li"
  title: "a.report-title"
  detail_link: "a.report-title"
  published_at: ".date"
  next_page: "a.next"

detail:
  institution: ".publisher"
  published_at: ".published-date"
  attachments: "a.download"
  license: ".license"

filters:
  allowed_extensions: [pdf, hwp, docx]
  include_title_keywords: []
  exclude_title_keywords: [채용, 입찰, 행사, 공고]
```

YAML로 해결되지 않는 예외만 전용 parser에 작성합니다.

---

## 21. Repository와 트랜잭션 경계

### 21.1 Repository 규칙

- 데이터베이스 쿼리를 pipeline이나 UI 컴포넌트에 작성하지 않습니다.
- repository는 저장·조회만 담당하고 선별 규칙을 판단하지 않습니다.
- 서비스는 repository 인터페이스에 의존합니다.
- Supabase 구현은 `repositories/supabase/` 아래에 둡니다.

### 21.2 주요 트랜잭션

#### 신규 항목 저장

```text
source_item upsert
→ document candidate 생성 또는 연결
→ document_source 생성
→ run count 갱신
```

#### 승인

```text
document 수정
→ workflow_status=APPROVED
→ review_action 기록
```

#### 공개

```text
publication 생성
→ publication_items 저장
→ snapshot 생성
→ digest 생성
→ 성공 시 현재 snapshot 포인터 교체
```

스냅샷 포인터는 모든 생성이 성공한 뒤 교체하여 중간 상태를 공개하지 않습니다.

---

## 22. 보안 설계

### 22.1 공개 데이터

- `feed_snapshots`의 현재 공개 스냅샷만 익명 읽기 허용
- `digest_files`의 공개 객체만 읽기 허용
- documents, review_actions, source_runs는 익명 접근 금지

### 22.2 관리자

- Supabase Auth 또는 동등한 관리자 인증
- 허용된 관리자 이메일 또는 역할 기반 접근
- 모든 쓰기 작업은 서버 측 세션 검증
- Service Role Key는 브라우저에 절대 노출하지 않음

### 22.3 수집 보안

- URL scheme은 HTTPS/HTTP만 허용
- 내부망·localhost·metadata IP로 향하는 URL 차단
- 다운로드 크기 상한 적용
- 리다이렉트 횟수 제한
- 파일명 정제
- HTML 표시 시 원문 HTML을 그대로 주입하지 않음

---

## 23. 성능 설계

### 23.1 공개 페이지

- 오늘 스냅샷은 서버 캐시 또는 정적 재검증 사용
- 최초 HTML에 기본 분야 데이터를 포함
- 카드 표지 이미지 미사용
- 아이콘은 인라인 SVG 또는 작은 아이콘 세트만 사용
- 클라이언트 상태는 active topic, range 정도로 제한
- 상태 관리 라이브러리 없이 React state와 작은 hook 사용

### 23.2 Collector

- 출처별 실행을 독립 task로 처리
- 같은 도메인 동시 요청 수 제한
- PDF 다운로드는 stream 처리
- 대용량 파일은 상한 초과 시 분석을 중단하고 공식 페이지 연결만 저장
- Playwright는 정적 HTTP로 실패한 출처에서만 사용

### 23.3 DB

주요 인덱스:

```text
source_items(source_id, source_item_key)
document_files(sha256)
documents(normalized_title, published_at)
documents(workflow_status, published_at)
document_topics(topic_id, score)
publication_items(publication_id, topic_id, rank)
feed_snapshots(is_current, range_key)
source_runs(source_id, started_at desc)
```

---

## 24. 관측성과 오류 처리

### 24.1 구조화 로그

```json
{
  "event": "source_run_completed",
  "source": "nars",
  "runId": "uuid",
  "durationMs": 5210,
  "discovered": 12,
  "new": 3,
  "failed": 0
}
```

### 24.2 오류 코드 예시

```text
SOURCE_LIST_UNREACHABLE
SOURCE_SELECTOR_MISSING
SOURCE_DETAIL_PARSE_FAILED
FILE_DOWNLOAD_FAILED
FILE_TOO_LARGE
FILE_INVALID_SIGNATURE
PDF_TEXT_EXTRACTION_FAILED
DUPLICATE_AMBIGUOUS
ANALYSIS_PROVIDER_FAILED
SNAPSHOT_BUILD_FAILED
DIGEST_BUILD_FAILED
```

### 24.3 출처 상태

- `HEALTHY`: 최근 실행 정상
- `DEGRADED`: 연속 2~3회 실패 또는 일부 파싱 실패
- `DISABLED`: 관리자 비활성화

전체 작업은 한 출처 실패로 중단하지 않습니다.

---

## 25. 테스트 전략

### 25.1 Collector

- parser unit test: 저장된 HTML fixture 사용
- file validation unit test: 정상·손상·HTML 위장 PDF fixture
- deduplication test: URL·해시·제목 유사도 조합
- pipeline integration test: 가상 출처 → 문서 → 검수 대기
- contract test: JSON Schema 검증
- live source test: CI 기본 제외, 별도 저빈도 smoke workflow

### 25.2 Web

- topic filter unit test
- localStorage 복원 test
- delivery mode에 따른 버튼 test
- snapshot schema validation test
- 관리자 action 권한 test
- Playwright E2E:
  - 첫 화면 표시
  - 분야 클릭
  - 최근 7일 전환
  - 파일 버튼 상태
  - 관리자 승인 후 스냅샷 반영

### 25.3 DB/RLS

- 익명 사용자가 공개 스냅샷만 읽을 수 있는지
- 익명 사용자가 documents와 review_actions에 접근할 수 없는지
- 관리자가 승인 작업을 수행할 수 있는지

---

## 26. CI 품질 게이트

모든 pull request에서 다음을 수행합니다.

```text
TypeScript typecheck
ESLint
Web unit/integration tests
Python Ruff
Python mypy 또는 pyright
pytest
JSON Schema validation
Source YAML validation
File size rule check
Migration lint/test
Build
```

실패한 테스트를 건너뛰거나 임시로 비활성화한 상태로 병합하지 않습니다.

---

## 27. 환경변수

```text
# Web
NEXT_PUBLIC_APP_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ADMIN_ALLOWED_EMAILS=

# Collector
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
TEMP_FILE_DIR=
MAX_DOWNLOAD_BYTES=
DEFAULT_REQUEST_DELAY_MS=
PLAYWRIGHT_ENABLED=true

# AI provider abstraction
ANALYSIS_PROVIDER=
ANALYSIS_API_KEY=
ANALYSIS_MODEL=

# Storage and digest
DIGEST_BUCKET=digests
TEMP_BUCKET=temporary-source-files
MIRROR_BUCKET=mirrored-source-files
```

실제 키는 저장소에 포함하지 않습니다.

---

## 28. 구현 순서

### Step 1. 계약과 DB

- enum·schema 확정
- migrations 작성
- 공개 snapshot schema 생성
- seed topics 작성

### Step 2. Collector 골격

- CLI
- adapter interface
- generic static/rendered/rss adapters
- repository interface
- fixture 기반 수집

### Step 3. 파일·중복 처리

- 다운로드 검증
- PDF 추출
- hash
- 중복 서비스
- 상태 머신

### Step 4. 관리자 검수

- auth
- review list
- inline editor
- approve/reject/merge

### Step 5. 공개 피드

- server snapshot load
- topic selector
- report card
- delivery actions
- localStorage

### Step 6. 분석·정리본

- mock provider 먼저 구현
- 실제 provider는 인터페이스 뒤에 연결
- digest HTML/PDF

### Step 7. 실제 출처

- 구조가 다른 3개 출처부터 구현
- 각 출처 fixture와 회귀 테스트 추가
- 이후 5개까지 확대

---

## 29. 구현 시 금지사항

- 외부 콘텐츠 수집에 공식·비공식 API 사용
- 숨겨진 JSON/XHR 주소 직접 호출
- 사이트 접근 제한·CAPTCHA 우회
- 모든 출처를 하나의 `collector.py`에 작성
- 모든 UI를 하나의 `page.tsx`에 작성
- 모든 타입을 하나의 `types.ts`에 작성
- 모든 SQL을 하나의 migration에 작성
- DB 쿼리를 React 컴포넌트에 작성
- 비즈니스 로직을 Route Handler에 작성
- 실시간 사용자 요청 중 AI 요약 실행
- 원본 PDF를 권리 확인 없이 영구 저장
- 공개 보고서 상세 페이지 추가
- 회원가입·마이페이지 추가
- “나중에 분리”를 전제로 거대 파일부터 작성

---

## 30. 최종 설계 판단

이 서비스의 내부 파이프라인은 여러 단계를 갖지만, 공개 사용자에게는 그 복잡성이 보여서는 안 됩니다.

```text
내부: 수집 → 검증 → 중복 → 분석 → 권리 → 검수 → 공개
외부: 분야 클릭 → 카드 확인 → 파일 받기
```

설계의 성공 기준은 다음과 같습니다.

- 공개 `page.tsx`가 얇고 읽기 쉬움
- 기관 하나를 추가할 때 기존 어댑터를 크게 수정하지 않음
- 파일·요약·권리 판단이 각각 독립 모듈임
- 공개 화면에서 내부 페이지 이동이 발생하지 않음
- 분야 전환이 네트워크 대기 없이 즉시 동작함
- 출처 하나가 깨져도 직전 공개 피드는 유지됨
- 어떤 사람이 코드를 열어도 기능 위치를 파일 트리만으로 예측할 수 있음
