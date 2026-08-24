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
  content_tag: string | null;
  primary_source_url: string;
  workflow_status: StoredDocument["workflowStatus"];
  created_at: string;
  updated_at: string;
  document_sources: { sources: { content_type: StoredDocument["sourceContentType"] | null }[] | null }[];
}

interface SnapshotShape {
  reportsByTopic?: { all?: unknown[] };
}

export function sortStoredDocuments(
  documents: StoredDocument[],
  contentType?: StoredDocument["sourceContentType"]
): StoredDocument[] {
  return [...documents].sort((left, right) => {
    // 1. Primary sort: publishedAt descending (null/unknown dates last)
    const leftDate = left.publishedAt && left.publishedAt !== "발행일 미상" ? left.publishedAt : "";
    const rightDate = right.publishedAt && right.publishedAt !== "발행일 미상" ? right.publishedAt : "";
    if (leftDate !== rightDate) {
      if (!leftDate) return 1;
      if (!rightDate) return -1;
      return rightDate.localeCompare(leftDate);
    }

    // 2. Secondary sort:
    // Press releases: created_at desc, then updated_at desc
    // Public reports: updated_at desc, then created_at desc
    if (contentType === "PRESS_RELEASE" || left.sourceContentType === "PRESS_RELEASE") {
      const createdCmp = (right.createdAt || "").localeCompare(left.createdAt || "");
      if (createdCmp !== 0) return createdCmp;
      return (right.updatedAt || "").localeCompare(left.updatedAt || "");
    }

    const updatedCmp = (right.updatedAt || "").localeCompare(left.updatedAt || "");
    if (updatedCmp !== 0) return updatedCmp;
    return (right.createdAt || "").localeCompare(left.createdAt || "");
  });
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
    .select("id,canonical_title,institution,published_at,content_tag,primary_source_url,workflow_status,created_at,updated_at,document_sources(sources(content_type))")
    .in("workflow_status", ["APPROVED", "PUBLISHED", "REJECTED"])
    .order("published_at", { ascending: false, nullsFirst: false })
    .order("created_at", { ascending: false })
    .limit(150);
  if (error) throw new Error("보관 문서를 불러오지 못했습니다.");

  const mapped: StoredDocument[] = (data as StoredDocumentRow[]).map((row) => ({
    id: row.id,
    canonicalTitle: row.canonical_title,
    institution: row.institution,
    publishedAt: row.published_at ?? "발행일 미상",
    primarySourceUrl: row.primary_source_url,
    workflowStatus: row.workflow_status,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    sourceContentType: resolveSourceContentType(row.document_sources, row.content_tag, row.institution),
  }));

  return sortStoredDocuments(mapped);
}
