import type { DigestLink } from "../types/public-feed";
import { DigestDownload } from "./digest-download";

export type ViewMode = "list" | "grid";

interface FeedSummaryProps {
  topic: string;
  topicId: string;
  count: number;
  digest?: DigestLink;
  archiveDate?: string | null;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

function description(topicId: string, count: number, archiveDate?: string | null): string {
  if (topicId === "press-release") {
    const dateLabel = archiveDate ? `${archiveDate.replaceAll("-", ".")} 발행 보도자료` : "보도자료";
    return `${dateLabel} ${count}건`;
  }
  if (topicId === "all") return `최근 7일 꼭 볼 자료 ${count}건`;
  return `최근 7일 선정 자료 ${count}건`;
}


export function FeedSummary({
  topic,
  topicId,
  count,
  digest,
  archiveDate,
  viewMode,
  onViewModeChange,
}: FeedSummaryProps) {
  return (
    <section className="feed-summary" aria-live="polite">
      <div className="feed-summary-left">
        <div>
          <h2>{topic}</h2>
          <p>{description(topicId, count, archiveDate)}</p>
        </div>
      </div>
      <div className="feed-summary-right">
        <div className="view-toggle" role="group" aria-label="보기 모드">
          <button
            type="button"
            className={`view-toggle-btn ${viewMode === "list" ? "is-active" : ""}`}
            onClick={() => onViewModeChange("list")}
            aria-pressed={viewMode === "list"}
          >
            <span>☰ 인덱스</span>
          </button>
          <button
            type="button"
            className={`view-toggle-btn ${viewMode === "grid" ? "is-active" : ""}`}
            onClick={() => onViewModeChange("grid")}
            aria-pressed={viewMode === "grid"}
          >
            <span>▦ 그리드</span>
          </button>
        </div>
        <DigestDownload digest={digest} topicLabel={topic} />
      </div>
    </section>
  );
}
