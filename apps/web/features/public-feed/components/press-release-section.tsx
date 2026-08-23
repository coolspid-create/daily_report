"use client";

import type { PublicReport } from "../types/public-report";
import { ReportActions } from "./report-actions";

interface PressReleaseSectionProps {
  reports: PublicReport[];
}

export function PressReleaseSection({ reports }: PressReleaseSectionProps) {
  if (reports.length === 0) return null;

  return (
    <section className="press-release-section" aria-label="최신 24시간 보도자료">
      <div className="press-section-header">
        <div className="press-title-wrap">
          <span className="press-icon" aria-hidden="true">📰</span>
          <h3>최신 24시간 정부·공공기관 보도자료</h3>
          <span className="press-live-badge">24H LIVE</span>
        </div>
        <span className="press-count">{reports.length}건</span>
      </div>
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
    </section>
  );
}
