"use client";

import { useState } from "react";
import type { ViewMode } from "./feed-summary";
import type { PublicReport } from "../types/public-report";
import { ReportActions } from "./report-actions";

interface PressReleaseSectionProps {
  reports: PublicReport[];
  archiveDate: string | null;
  viewMode?: ViewMode;
}

function archiveLabel(date: string | null): string {
  return date ? `${date.replaceAll("-", ".")} 발행본` : "보도자료";
}

export function PressReleaseSection({
  reports,
  archiveDate,
  viewMode = "list",
}: PressReleaseSectionProps) {
  if (reports.length === 0) {
    return (
      <section className="empty-feed" aria-live="polite">
        <p>{archiveLabel(archiveDate)}에 보도자료가 없습니다.</p>
      </section>
    );
  }

  return (
    <section className="press-release-section" aria-label={`${archiveLabel(archiveDate)} 보도자료`}>
      <div className="press-section-header">
        <div className="press-title-wrap">
          <span className="press-icon" aria-hidden="true">📰</span>
          <h3>{archiveLabel(archiveDate)} 중앙부처·공공기관 메인 보도자료</h3>
        </div>
        <span className="press-count">{reports.length}건</span>
      </div>

      {viewMode === "list" ? (
        <div className="press-list">
          {reports.map((report) => (
            <PressReleaseItem key={report.id} report={report} viewMode="list" />
          ))}
        </div>
      ) : (
        <div className="press-grid">
          {reports.map((report) => (
            <PressReleaseItem key={report.id} report={report} viewMode="grid" />
          ))}
        </div>
      )}
    </section>
  );
}

interface PressReleaseItemProps {
  report: PublicReport;
  viewMode: ViewMode;
}

function PressReleaseItem({ report, viewMode }: PressReleaseItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const canExpand = Boolean(report.shortSummary);
  const toggleLabel = isExpanded ? "요약 접기" : "더보기";
  const titleId = `press-title-${report.id}`;
  const summaryId = `press-summary-${report.id}`;
  const toggle = () => setIsExpanded((current) => !current);

  const summary = report.shortSummary ? (
    <div id={summaryId} className="press-summary-expanded">
      <span className="why-matters-label">WHY IT MATTERS</span>
      <p className="why-matters-text">{report.shortSummary}</p>
      {report.analysisAvailable !== false && report.keyTags.length > 0 ? (
        <div className="tag-list">
          {report.keyTags.map((tag) => (
            <span key={tag} className="tag-item">#{tag}</span>
          ))}
        </div>
      ) : null}
    </div>
  ) : null;

  const title = (
    <button
      type="button"
      className="press-summary-trigger"
      onClick={toggle}
      aria-expanded={isExpanded}
      aria-controls={canExpand ? summaryId : undefined}
      disabled={!canExpand}
    >
      {report.title}
    </button>
  );

  const toggleButton = canExpand ? (
    <button
      type="button"
      className={`btn-action btn-action-toggle ${isExpanded ? "is-open" : ""}`}
      onClick={toggle}
      aria-expanded={isExpanded}
      aria-controls={summaryId}
    >
      {toggleLabel}
    </button>
  ) : null;

  if (viewMode === "grid") {
    return (
      <article className="press-card" aria-labelledby={titleId}>
        <div className="press-card-meta">
          <span className="press-inst-badge">{report.institution}</span>
          <time dateTime={report.publishedAt} className="press-date">{report.publishedAt}</time>
        </div>
        <h4 id={titleId} className="press-card-title">{report.title}</h4>
        {summary}
        <div className="press-card-footer">
          <ReportActions file={report.file} />
        </div>
      </article>
    );
  }

  return (
    <article className="press-list-item" aria-labelledby={titleId}>
      <div className="press-list-main">
        <div className="press-list-meta">
          <span className="press-inst-badge">{report.institution}</span>
          <time dateTime={report.publishedAt} className="press-date">{report.publishedAt}</time>
        </div>
        <h4 id={titleId} className="press-list-title">{title}</h4>
        {isExpanded ? summary : null}
      </div>
      <div className="press-list-actions">
        <ReportActions file={report.file} />
        {toggleButton}
      </div>
    </article>
  );
}
