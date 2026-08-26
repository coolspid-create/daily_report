import { primaryAction } from "../lib/report-action";
import type { ReportFile } from "../types/public-report";

interface ReportActionsProps {
  file: ReportFile;
}

const externalProps = { target: "_blank", rel: "noopener noreferrer" } as const;

export function ReportActions({ file }: ReportActionsProps) {
  const primary = primaryAction(file);
  const hasSeparateSource = primary?.url !== file.sourceUrl;
  return (
    <div className="report-actions">
      {hasSeparateSource && (
        <a className="btn-action" href={file.sourceUrl} aria-label="원문 ↗ 공식 원문 열기" {...externalProps}>
          원문 ↗ <span className="sr-only">(새 창)</span>
        </a>
      )}
      {primary ? (
        <a
          className="btn-action btn-action-primary"
          href={primary.url}
          download={primary.download || undefined}
          aria-label={`${primary.label} 파일 다운로드`}
          {...externalProps}
        >
          {primary.label} <span className="sr-only">(새 창)</span>
        </a>
      ) : null}
    </div>
  );
}
