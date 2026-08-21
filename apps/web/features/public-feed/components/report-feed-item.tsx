"use client";

import { useId, useState } from "react";
import type { PublicReport } from "../types/public-report";
import { ReportActions } from "./report-actions";
import { ReportMeta } from "./report-meta";
import { ReportTags } from "./report-tags";

interface ReportFeedItemProps {
  report: PublicReport;
}

export function ReportFeedItem({ report }: ReportFeedItemProps) {
  const hasAnalysis = report.analysisAvailable !== false;
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const summaryId = useId();

  return (
    <article className="report-feed-item" aria-labelledby={`report-${report.id}`}>
      <div className="report-item-topline">
        {report.isNew && <span className="badge badge-new">NEW</span>}
        {hasAnalysis && <span className="badge">{report.contentTag}</span>}
      </div>
      <h3 id={`report-${report.id}`}>{report.title}</h3>
      <ReportMeta institution={report.institution} publishedAt={report.publishedAt} file={report.file} />
      {report.shortSummary && (
        <div className="report-summary-block">
          <p id={summaryId} className={`report-summary${summaryExpanded ? " is-expanded" : ""}`}>
            {report.shortSummary}
          </p>
          <button
            type="button"
            className="summary-toggle"
            aria-expanded={summaryExpanded}
            aria-controls={summaryId}
            onClick={() => setSummaryExpanded((value) => !value)}
          >
            {summaryExpanded ? "요약 접기" : "더보기"}
          </button>
        </div>
      )}
      <div className="report-item-bottom">
        {hasAnalysis && <ReportTags tags={report.keyTags} />}
        <ReportActions file={report.file} />
      </div>
    </article>
  );
}
