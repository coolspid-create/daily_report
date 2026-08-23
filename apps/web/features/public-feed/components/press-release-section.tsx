"use client";

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
            <article key={report.id} className="press-list-item">
              <div className="press-list-main">
                <div className="press-list-meta">
                  <span className="press-inst-badge">{report.institution}</span>
                  <time dateTime={report.publishedAt} className="press-date">
                    {report.publishedAt}
                  </time>
                </div>
                <h4 className="press-list-title">
                  <a
                    href={report.file.downloadUrl || report.file.sourceUrl}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {report.title}
                  </a>
                </h4>
                {report.shortSummary ? (
                  <p className="press-list-summary">{report.shortSummary}</p>
                ) : null}
              </div>
              <div className="press-list-actions">
                <ReportActions file={report.file} />
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="press-grid">
          {reports.map((report) => (
            <article key={report.id} className="press-card">
              <div className="press-card-meta">
                <span className="press-inst-badge">{report.institution}</span>
                <time dateTime={report.publishedAt} className="press-date">
                  {report.publishedAt}
                </time>
              </div>
              <h4 className="press-card-title">
                <a
                  href={report.file.downloadUrl || report.file.sourceUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {report.title}
                </a>
              </h4>
              {report.shortSummary ? (
                <p className="press-card-summary">{report.shortSummary}</p>
              ) : null}
              <div className="press-card-footer">
                <ReportActions file={report.file} />
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
