import type { PublicReport } from "../types/public-report";
import { EmptyFeed } from "./empty-feed";
import { ReportFeedItem, type ViewMode } from "./report-feed-item";

interface ReportListProps {
  reports: PublicReport[];
  topicLabel: string;
  viewMode: ViewMode;
}

export function ReportList({ reports, topicLabel, viewMode }: ReportListProps) {
  if (reports.length === 0) return <EmptyFeed topicLabel={topicLabel} />;

  return (
    <div className={`report-list view-${viewMode}`}>
      {reports.map((report, idx) => (
        <ReportFeedItem
          key={report.id}
          report={report}
          index={idx + 1}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
}
