import { createServiceClient } from "@/lib/database/service-client";
import type { PublicationHistory, StoredDocument } from "../types/admin-review";
import { resolveSourceContentType } from "./source-content-type";

interface PublicationRow {
  publication_date: string;
  published_at: string | null;
  feed_snapshots: { created_at: string; snapshot_json: unknown }[];
}

interface StoredDocumentRow {
  id: string;
  canonical_title: string;
  institution: string;
  published_at: string | null;
  primary_source_url: string;
  workflow_status: StoredDocument["workflowStatus"];
  updated_at: string;
  document_sources: { sources: { content_type: StoredDocument["sourceContentType"] | null }[] | null }[];
}

interface SnapshotShape {
  reportsByTopic?: { all?: unknown[] };
}

export async function getPublicationHistory(): Promise<PublicationHistory[]> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("daily_publications")
    .select("publication_date,published_at,feed_snapshots(created_at,snapshot_json)")
    .eq("range_key", "7d")
    .eq("status", "PUBLISHED")
    .order("publication_date", { ascending: false })
    .limit(31);
  if (error) throw new Error("발행 이력을 불러오지 못했습니다.");

  return (data as PublicationRow[]).map((row) => {
    const snapshot = [...row.feed_snapshots].sort((left, right) =>
      right.created_at.localeCompare(left.created_at),
    )[0]?.snapshot_json as SnapshotShape | undefined;
    return {
      publicationDate: row.publication_date,
      publishedAt: row.published_at,
      reportCount: snapshot?.reportsByTopic?.all?.length ?? 0,
    };
  });
}

export async function getStoredDocuments(): Promise<StoredDocument[]> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("documents")
    .select("id,canonical_title,institution,published_at,primary_source_url,workflow_status,updated_at,document_sources(sources(content_type))")
    .in("workflow_status", ["APPROVED", "REJECTED"])
    .order("updated_at", { ascending: false })
    .limit(80);
  if (error) throw new Error("보관 문서를 불러오지 못했습니다.");

  return (data as StoredDocumentRow[]).map((row) => ({
    id: row.id,
    canonicalTitle: row.canonical_title,
    institution: row.institution,
    publishedAt: row.published_at ?? "발행일 미상",
    primarySourceUrl: row.primary_source_url,
    workflowStatus: row.workflow_status,
    updatedAt: row.updated_at,
    sourceContentType: resolveSourceContentType(row.document_sources),
  }));
}
