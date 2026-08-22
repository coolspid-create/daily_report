"use client";

import { useState } from "react";
import type { PublicReport } from "../types/public-report";
import { primaryAction } from "../lib/report-action";

export type ViewMode = "list" | "grid";

interface ReportFeedItemProps {
  report: PublicReport;
  index?: number;
  viewMode?: ViewMode;
}

const externalProps = { target: "_blank", rel: "noopener noreferrer" } as const;

export function ReportFeedItem({ report, index = 1, viewMode = "list" }: ReportFeedItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const primary = primaryAction(report.file);
  const formattedIndex = String(index).padStart(2, "0");
  const hasAnalysis = report.analysisAvailable !== false;

  if (viewMode === "grid") {
    return (
      <article className="grid-card" aria-labelledby={`report-title-${report.id}`}>
        <div className="grid-card-top">
          <div className="grid-card-top-left">
            <span className="grid-card-num">{formattedIndex}</span>
            <span className="index-inst-badge">{report.institution}</span>
            {report.isNew && (
              <span className="tag-item" style={{ color: "var(--color-accent)", borderColor: "var(--color-accent)" }}>
                NEW
              </span>
            )}
          </div>
          <span className="index-date">{report.publishedAt}</span>
        </div>

        <h3 id={`report-title-${report.id}`}>
          <a href={report.file.sourceUrl} {...externalProps}>
            {report.title}
          </a>
        </h3>

        {report.shortSummary && (
          <div className="why-matters-box">
            <span className="why-matters-label">WHY IT MATTERS</span>
            <p className="why-matters-text">{report.shortSummary}</p>
          </div>
        )}

        <div className="grid-card-bottom">
          <div className="tag-list">
            {hasAnalysis &&
              report.keyTags.map((tag) => (
                <span key={tag} className="tag-item">
                  #{tag}
                </span>
              ))}
          </div>
          <div className="grid-card-actions">
            {report.file.sourceUrl && (
              <a className="btn-action" href={report.file.sourceUrl} aria-label="공식 출처 열기" {...externalProps}>
                원문 ↗
              </a>
            )}
            {primary && (
              <a
                className="btn-action btn-action-primary"
                href={primary.url}
                download={primary.download || undefined}
                aria-label="PDF 다운로드"
                {...externalProps}
              >
                PDF ↓
              </a>
            )}
          </div>
        </div>
      </article>
    );
  }

  return (
    <div className="index-row-container">
      <div
        className="index-row"
        onClick={() => setIsExpanded((prev) => !prev)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
        aria-expanded={isExpanded}
      >
        <span className="index-num">{formattedIndex}</span>
        <span className="index-inst-badge" title={report.institution}>
          {report.institution}
        </span>
        <div className="index-title-col">
          <span className="index-title" title={report.title}>
            {report.title}
          </span>
          {report.isNew && (
            <span className="tag-item" style={{ color: "var(--color-accent)", borderColor: "var(--color-accent)" }}>
              NEW
            </span>
          )}
        </div>
        <span className="index-date">{report.publishedAt}</span>
        <div className="index-actions" onClick={(e) => e.stopPropagation()}>
          {report.file.sourceUrl ? (
            <a className="btn-action" href={report.file.sourceUrl} aria-label="공식 출처 열기" {...externalProps}>
              원문 ↗
            </a>
          ) : (
            <span className="btn-action-placeholder" aria-hidden="true" />
          )}

          {primary ? (
            <a
              className="btn-action btn-action-primary"
              href={primary.url}
              download={primary.download || undefined}
              aria-label="PDF 파일 다운로드"
              {...externalProps}
            >
              PDF ↓
            </a>
          ) : (
            <span className="btn-action-placeholder" aria-hidden="true" />
          )}

          {report.shortSummary ? (
            <button
              type="button"
              className={`btn-action btn-action-toggle ${isExpanded ? "is-open" : ""}`}
              onClick={() => setIsExpanded((prev) => !prev)}
              aria-expanded={isExpanded}
              aria-label={isExpanded ? "요약 접기" : "더보기"}
            >
              {isExpanded ? "요약 접기" : "더보기"}
            </button>
          ) : (
            <span className="btn-action-placeholder" aria-hidden="true" />
          )}
        </div>
      </div>

      {isExpanded && report.shortSummary && (
        <div className="index-accordion" onClick={(e) => e.stopPropagation()}>
          <div className="why-matters-box">
            <span className="why-matters-label">WHY IT MATTERS</span>
            <p className="why-matters-text">{report.shortSummary}</p>
          </div>
          {hasAnalysis && report.keyTags.length > 0 && (
            <div className="tag-list">
              {report.keyTags.map((tag) => (
                <span key={tag} className="tag-item">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
