import { createServiceClient } from "@/lib/database/service-client";
import type { ReviewItem } from "../types/admin-review";

interface ReviewRow {
  id: string;
  canonical_title: string;
  institution: string;
  published_at: string | null;
  primary_topic_id: string | null;
  content_tag: string | null;
  why_it_matters: string | null;
  delivery_mode: ReviewItem["deliveryMode"];
  workflow_status: ReviewItem["workflowStatus"];
  primary_source_url: string;
  document_analysis: { key_tags: string[] } | null;
  document_files: { sha256: string | null }[];
  review_actions: { action: string; after_data: { reasonCodes?: string[] } | null }[];
}

export async function getReviewItems(): Promise<ReviewItem[]> {
  const client = createServiceClient();
  const today = new Date();
  const cutoff = new Date(today);
  cutoff.setDate(cutoff.getDate() - 7);
  const { data, error } = await client
    .from("documents")
    .select("*,document_analysis(key_tags),document_files(sha256),review_actions(action,after_data)")
    .in("workflow_status", ["NEW", "NEEDS_REVIEW"])
    .gte("published_at", cutoff.toISOString().slice(0, 10))
    .lte("published_at", today.toISOString().slice(0, 10))
    .order("created_at", { ascending: false });
  if (error) throw new Error("검수 목록을 불러오지 못했습니다.");
  const rows = data as ReviewRow[];
  const idsByHash = new Map<string, string[]>();
  for (const row of rows) {
    for (const file of row.document_files) {
      if (!file.sha256) continue;
      idsByHash.set(file.sha256, [...(idsByHash.get(file.sha256) ?? []), row.id]);
    }
  }
  return rows.map((row) => ({
    id: row.id,
    canonicalTitle: row.canonical_title,
    institution: row.institution,
    publishedAt: row.published_at ?? "",
    primaryTopicId: row.primary_topic_id ?? "industry",
    contentTag: row.content_tag ?? "검수 필요",
    whyItMatters: row.why_it_matters ?? "관리자 검수가 필요합니다.",
    keyTags: row.document_analysis?.key_tags ?? ["검수 필요"],
    deliveryMode: row.delivery_mode,
    workflowStatus: row.workflow_status,
    primarySourceUrl: row.primary_source_url,
    duplicateCandidateIds: [
      ...new Set(
        row.document_files.flatMap((file) =>
          file.sha256 ? idsByHash.get(file.sha256) ?? [] : [],
        ),
      ),
    ].filter((id) => id !== row.id),
    exceptionReasons: row.review_actions
      .filter((action) => action.action === "AUTO_HOLD")
      .flatMap((action) => action.after_data?.reasonCodes ?? []),
  }));
}
