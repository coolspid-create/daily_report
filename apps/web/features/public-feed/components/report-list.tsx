import type { PublicReport } from "../types/public-report";
import { EmptyFeed } from "./empty-feed";
import { ReportFeedItem } from "./report-feed-item";

interface ReportListProps {
  reports: PublicReport[];
  topicLabel: string;
}

export function ReportList({ reports, topicLabel }: ReportListProps) {
  if (reports.length === 0) return <EmptyFeed topicLabel={topicLabel} />;
  return <div className="report-list">{reports.map((report) => <ReportFeedItem key={report.id} report={report} />)}</div>;
}
