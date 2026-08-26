import { createServiceClient } from "@/lib/database/service-client";
import type { PublicReport, SourceContentType } from "../types/public-report";
import type { PublicPressArchive, PublicPressArchiveDate } from "../types/public-feed";

const PRESS_ARCHIVE_LIMIT = 31;

interface SourceRow {
  sources: { content_type: SourceContentType | null }[] | null;
}

interface PressDocumentRow {
  id: string;
  canonical_title: string;
  institution: string;
  published_at: string | null;
  content_tag: string | null;
  why_it_matters: string | null;
  primary_source_url: string;
  delivery_mode: PublicReport["file"]["deliveryMode"];
  created_at: string;
  updated_at: string;
  document_analysis: { summary_kind: string; key_tags: string[] | null }[] | null;
  document_files: {
    file_url: string;
    extension: string | null;
    size_bytes: number | null;
    page_count: number | null;
    validation_status: string;
    created_at: string;
  }[] | null;
  document_sources: SourceRow[];
}

function isPressReleaseRow(row: PressDocumentRow): boolean {
  const explicitTypes: SourceContentType[] = [];
  for (const src of row.document_sources ?? []) {
    const items = src.sources;
    if (Array.isArray(items)) {
      explicitTypes.push(...items.flatMap((s) => s?.content_type ? [s.content_type] : []));
    } else if (items && (items as { content_type?: string }).content_type === "PRESS_RELEASE") {
      explicitTypes.push("PRESS_RELEASE");
    } else if (items && (items as { content_type?: string }).content_type === "REPORT") {
      explicitTypes.push("REPORT");
    }
  }
  if (explicitTypes.includes("PRESS_RELEASE")) return true;
  if (explicitTypes.includes("REPORT")) return false;
  return row.content_tag === "보도자료" || row.institution.includes("보도자료");
}

function latestValidFile(row: PressDocumentRow) {
  return (row.document_files ?? [])
    .filter((file) => file.validation_status === "VALID")
    .sort((left, right) => right.created_at.localeCompare(left.created_at))[0] ?? null;
}

export function toPublicReport(row: PressDocumentRow): PublicReport {
  const analysis = row.document_analysis?.[0] ?? null;
  const file = latestValidFile(row);
  return {
    id: row.id,
    title: row.canonical_title,
    institution: row.institution,
    publishedAt: row.published_at ?? row.created_at.slice(0, 10),
    contentTag: row.content_tag ?? "보도자료",
    isNew: true,
    analysisAvailable: Boolean(analysis && analysis.summary_kind !== "UNAVAILABLE"),
    shortSummary: analysis?.summary_kind === "UNAVAILABLE" ? null : row.why_it_matters,
    keyTags: analysis?.key_tags?.slice(0, 3) ?? ["보도자료"],
    file: {
      format: file?.extension?.toUpperCase() ?? null,
      sizeBytes: file?.size_bytes ?? null,
      pageCount: file?.page_count ?? null,
      deliveryMode: row.delivery_mode,
      downloadUrl: file?.file_url ?? null,
      sourceUrl: row.primary_source_url,
    },
    sourceContentType: "PRESS_RELEASE",
  };
}

function publicationDate(row: PressDocumentRow): string {
  return (row.published_at ?? row.created_at).slice(0, 10);
}

type PressArchiveByDate = Record<string, PublicPressArchiveDate>;

async function loadPressReportsByDate(): Promise<PressArchiveByDate> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("documents")
    .select("id,canonical_title,institution,published_at,content_tag,why_it_matters,primary_source_url,delivery_mode,created_at,updated_at,document_analysis(summary_kind,key_tags),document_files(file_url,extension,size_bytes,page_count,validation_status,created_at),document_sources(sources(content_type))")
    .in("workflow_status", ["APPROVED", "PUBLISHED"])
    .order("published_at", { ascending: false, nullsFirst: false })
    .order("created_at", { ascending: false })
    .limit(250);

  if (error) throw new Error("보도자료를 불러오지 못했습니다.");
  const reportsByDate: PressArchiveByDate = {};
  for (const row of data as PressDocumentRow[]) {
    if (!isPressReleaseRow(row)) continue;
    const date = publicationDate(row);
    const entry = (reportsByDate[date] ??= { reports: [], generatedAt: null });
    entry.reports.push(toPublicReport(row));
    if (!entry.generatedAt || row.updated_at > entry.generatedAt) {
      entry.generatedAt = row.updated_at;
    }
  }
  return reportsByDate;
}

function latestDates(reportsByDate: PressArchiveByDate): string[] {
  return Object.keys(reportsByDate).sort((left, right) => right.localeCompare(left)).slice(0, PRESS_ARCHIVE_LIMIT);
}

export async function getPublicPressArchive(preferredDate?: string | null): Promise<PublicPressArchive> {
  const reportsByDate = await loadPressReportsByDate();
  const dates = latestDates(reportsByDate);
  const currentDate = dates[0] ?? null;
  const loadedDate = preferredDate && dates.includes(preferredDate) ? preferredDate : currentDate;
  const loaded = loadedDate ? reportsByDate[loadedDate] : null;
  return {
    currentDate,
    dates,
    loadedDate,
    reports: loaded?.reports ?? [],
    generatedAt: loaded?.generatedAt ?? null,
  };
}

export async function getPublicPressArchiveDate(date: string): Promise<PublicPressArchiveDate | null> {
  const reportsByDate = await loadPressReportsByDate();
  return reportsByDate[date] ?? null;
}
