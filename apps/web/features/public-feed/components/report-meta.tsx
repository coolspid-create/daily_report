import type { ReportFile } from "../types/public-report";

interface ReportMetaProps {
  institution: string;
  publishedAt: string;
  file: ReportFile;
}

function formatBytes(value?: number | null): string | null {
  if (value == null) return null;
  return value >= 1_048_576 ? `${(value / 1_048_576).toFixed(1)}MB` : `${Math.ceil(value / 1024)}KB`;
}

export function ReportMeta({ institution, publishedAt, file }: ReportMetaProps) {
  const values = [institution, publishedAt, file.format, file.pageCount ? `${file.pageCount}쪽` : null, formatBytes(file.sizeBytes)];
  return (
    <p className="report-meta">
      {values.filter(Boolean).map((value) => <span key={value}>{value}</span>)}
    </p>
  );
}
