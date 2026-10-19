import { createServiceClient } from "@/lib/database/service-client";
import type { PublicReport } from "../types/public-report";
import type { PublicPressArchive, PublicPressArchiveDate } from "../types/public-feed";
import { loadArchiveDates } from "./load-archive-dates";

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

export async function getPublicPressArchiveDate(date: string): Promise<PublicPressArchiveDate | null> {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  const start = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(start.getTime()) || start.toISOString().slice(0, 10) !== date) return null;
  const nextDate = new Date(start.getTime() + 86400000).toISOString().slice(0, 10);
  const client = createServiceClient();
  const rows: PressDocumentRow[] = [];
  const pageSize = 250;
  for (let offset = 0; ; offset += pageSize) {
    const { data, error } = await client
      .from("documents")
      .select("id,canonical_title,institution,published_at,content_tag,why_it_matters,primary_source_url,delivery_mode,created_at,updated_at,document_analysis(summary_kind,key_tags),document_files(file_url,extension,size_bytes,page_count,validation_status,created_at),document_sources!inner(sources!inner(content_type))")
      .in("workflow_status", ["APPROVED", "PUBLISHED"])
      .eq("document_sources.sources.content_type", "PRESS_RELEASE")
      .or(`published_at.eq.${date},and(published_at.is.null,created_at.gte.${date}T00:00:00Z,created_at.lt.${nextDate}T00:00:00Z)`)
      .order("published_at", { ascending: false, nullsFirst: false })
      .order("created_at", { ascending: false })
      .order("id", { ascending: false })
      .range(offset, offset + pageSize - 1);
    if (error) throw new Error("보도자료를 불러오지 못했습니다.");
    rows.push(...data as unknown as PressDocumentRow[]);
    if (data.length < pageSize) break;
  }
  if (!rows.length) return null;
  return {
    reports: rows.map(toPublicReport),
    generatedAt: rows.reduce((latest, row) => row.updated_at > latest ? row.updated_at : latest, rows[0].updated_at),
  };
}

export async function getPublicPressArchive(preferredDate?: string | null): Promise<PublicPressArchive> {
  const dates = await loadArchiveDates(createServiceClient(), "press_archive_dates_page");
  const currentDate = dates[0] ?? null;
  const loadedDate = preferredDate && dates.includes(preferredDate) ? preferredDate : currentDate;
  const loaded = loadedDate ? await getPublicPressArchiveDate(loadedDate) : null;
  return {
    currentDate,
    dates,
    loadedDate,
    reports: loaded?.reports ?? [],
    generatedAt: loaded?.generatedAt ?? null,
  };
}
