import type { ReviewItem } from "../types/admin-review";

const REASON_LABELS: Record<string, string> = {
  OUTSIDE_COLLECTION_WINDOW: "최근 24시간 밖에서 수집됨",
  PUBLISHED_DATE_MISSING: "발행일 없음",
  PUBLISHED_DATE_OUTSIDE_WINDOW: "발행일이 대상 기간 밖임",
  SOURCE_UNHEALTHY: "출처 상태 확인 필요",
  RIGHTS_REVIEW_REQUIRED: "권리 검토 필요",
  DELIVERY_BLOCKED: "전달 차단 상태",
  SUMMARY_INCOMPLETE: "요약 미완료",
  SUMMARY_UNAVAILABLE: "본문 요약 없음",
  SUMMARY_EMPTY: "요약 내용 없음",
  KEY_TAGS_INVALID: "키워드 확인 필요",
  CONFIDENCE_LOW: "분석 신뢰도 낮음",
  SOURCE_URL_INVALID: "공식 링크 확인 필요",
  SESSION_FILE_URL: "만료 가능 파일 링크",
  DUPLICATE_CANDIDATE: "중복 후보",
};

interface ReviewListProps {
  items: ReviewItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

export function ReviewList({ items, activeId, onSelect }: ReviewListProps) {
  return (
    <div className="review-list" aria-label="검수 문서 목록">
      {items.map((item) => (
        <button key={item.id} type="button" className="review-list-item" aria-pressed={activeId === item.id} onClick={() => onSelect(item.id)}>
          <span className="badge">{item.workflowStatus}</span>
          <strong>{item.canonicalTitle}</strong>
          <small>{item.institution} · {item.publishedAt}</small>
          {item.exceptionReasons.length > 0 && <small>예외 사유: {item.exceptionReasons.map((reason) => REASON_LABELS[reason] ?? reason).join(", ")}</small>}
          {item.duplicateCandidateIds.length > 0 && <small>중복 후보 {item.duplicateCandidateIds.length}건</small>}
        </button>
      ))}
    </div>
  );
}
