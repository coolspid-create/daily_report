export type DeliveryMode =
  | "DIRECT_OFFICIAL_FILE"
  | "OFFICIAL_PAGE_ONLY"
  | "MIRRORED_ALLOWED"
  | "SUMMARY_ONLY"
  | "BLOCKED";

export interface ReportFile {
  format: string | null;
  sizeBytes?: number | null;
  pageCount?: number | null;
  deliveryMode: DeliveryMode;
  downloadUrl?: string | null;
  sourceUrl: string;
}

export interface PublicReport {
  id: string;
  title: string;
  institution: string;
  publishedAt: string;
  contentTag: string;
  isNew: boolean;
  analysisAvailable?: boolean;
  shortSummary: string | null;
  keyTags: string[];
  file: ReportFile;
}
