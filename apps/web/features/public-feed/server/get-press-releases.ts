import { createServiceClient } from "@/lib/database/service-client";
import type { PublicReport, SourceContentType } from "../types/public-report";

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
  document_analysis: { summary_kind: string; key_tags: string[] | null }[];
  document_files: {
    file_url: string;
    extension: string | null;
    size_bytes: number | null;
    page_count: number | null;
    validation_status: string;
    created_at: string;
  }[];
  document_sources: SourceRow[];
}

function contentTypeFor(sources: SourceRow[]): SourceContentType {
  return sources
    .flatMap((source) => source.sources ?? [])
    .find((source) => source.content_type)?.content_type ?? "REPORT";
}

function latestValidFile(row: PressDocumentRow) {
  return row.document_files
    .filter((file) => file.validation_status === "VALID")
    .sort((left, right) => right.created_at.localeCompare(left.created_at))[0] ?? null;
}

function toPublicReport(row: PressDocumentRow): PublicReport {
  const analysis = row.document_analysis[0] ?? null;
  const file = latestValidFile(row);
  return {
    id: row.id,
    title: row.canonical_title,
    institution: row.institution,
    publishedAt: row.published_at ?? row.created_at.slice(0, 10),
    contentTag: row.content_tag ?? "보도자료",
    isNew: true,
    analysisAvailable: analysis?.summary_kind !== "UNAVAILABLE",
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

export async function getLatestPressReleases(): Promise<PublicReport[]> {
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const client = createServiceClient();
  const { data, error } = await client
    .from("documents")
    .select("id,canonical_title,institution,published_at,content_tag,why_it_matters,primary_source_url,delivery_mode,created_at,document_analysis(summary_kind,key_tags),document_files(file_url,extension,size_bytes,page_count,validation_status,created_at),document_sources(sources(content_type))")
    .in("workflow_status", ["APPROVED", "PUBLISHED"])
    .gte("created_at", cutoff)
    .order("created_at", { ascending: false })
    .limit(60);

  if (error) throw new Error("보도자료를 불러오지 못했습니다.");
  return (data as PressDocumentRow[])
    .filter((row) => contentTypeFor(row.document_sources) === "PRESS_RELEASE")
    .map(toPublicReport);
}
