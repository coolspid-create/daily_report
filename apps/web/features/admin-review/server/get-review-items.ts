import { createServiceClient } from "@/lib/database/service-client";
import type { ReviewItem } from "../types/admin-review";
import { isWithinReviewWindow } from "../lib/review-eligibility";
import { resolveSourceContentType } from "./source-content-type";

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
  created_at: string;
  document_analysis: { key_tags: string[] } | null;
  document_files: { sha256: string | null }[];
  review_actions: { action: string; after_data: { reasonCodes?: string[] } | null }[];
  document_sources: { sources: { content_type: ReviewItem["sourceContentType"] | null }[] | null }[];
}

export async function getReviewItems(): Promise<ReviewItem[]> {
  const client = createServiceClient();
  const now = new Date();
  const cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const { data, error } = await client
    .from("documents")
    .select("*,document_analysis(key_tags),document_files(sha256),review_actions(action,after_data),document_sources(sources(content_type))")
    .in("workflow_status", ["NEW", "NEEDS_REVIEW"])
    .gte("created_at", cutoff)
    .order("created_at", { ascending: false });
  if (error) throw new Error("검수 목록을 불러오지 못했습니다.");
  const rows = (data as ReviewRow[]).map((row) => ({
    row,
    sourceContentType: resolveSourceContentType(row.document_sources, row.content_tag, row.institution),
  })).filter(({ row, sourceContentType }) => isWithinReviewWindow(sourceContentType, row.created_at, now));
  const idsByHash = new Map<string, string[]>();
  for (const { row } of rows) {
    for (const file of row.document_files) {
      if (!file.sha256) continue;
      idsByHash.set(file.sha256, [...(idsByHash.get(file.sha256) ?? []), row.id]);
    }
  }
  return rows.map(({ row, sourceContentType }) => ({
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
    createdAt: row.created_at,
    sourceContentType,
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
