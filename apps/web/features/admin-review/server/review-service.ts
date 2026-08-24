import type { User } from "@supabase/supabase-js";
import { createServiceClient } from "@/lib/database/service-client";
import { batchApproveSchema, mergeSchema, rejectSchema, reviewFormSchema } from "../schemas/review-form.schema";
import type { SourceContentType } from "../types/admin-review";
import { isBulkApprovalEligible } from "../lib/review-eligibility";
import { resolveSourceContentType } from "./source-content-type";

interface BatchReviewRow {
  id: string;
  created_at: string;
  published_at: string | null;
  content_tag: string | null;
  institution: string;
  document_sources: { sources: { content_type: SourceContentType | null }[] | null }[];
}

async function recordAction(documentId: string, user: User, action: string, after: object, reason?: string) {
  const client = createServiceClient();
  const { error } = await client.from("review_actions").insert({
    document_id: documentId,
    actor_id: user.id,
    action,
    after_data: after,
    reason: reason ?? null,
  });
  if (error) throw new Error("감사 기록 저장에 실패했습니다.");
}

export async function updateReview(documentId: string, payload: unknown, user: User) {
  const value = reviewFormSchema.parse(payload);
  const client = createServiceClient();
  const { error } = await client.from("documents").update({
    canonical_title: value.canonicalTitle,
    institution: value.institution,
    published_at: value.publishedAt,
    primary_topic_id: value.primaryTopicId,
    content_tag: value.contentTag,
    why_it_matters: value.whyItMatters,
    delivery_mode: value.deliveryMode,
    workflow_status: "NEEDS_REVIEW",
  }).eq("id", documentId);
  if (error) throw new Error("문서 수정에 실패했습니다.");
  await client.from("document_analysis").update({ key_tags: value.keyTags }).eq("document_id", documentId);
  await recordAction(documentId, user, "UPDATE", value);
  return value;
}

export async function approveReview(documentId: string, user: User) {
  const client = createServiceClient();
  const { error } = await client.from("documents").update({ workflow_status: "APPROVED" }).eq("id", documentId);
  if (error) throw new Error("승인에 실패했습니다.");
  await recordAction(documentId, user, "APPROVE", { workflowStatus: "APPROVED" });
}

export async function approveReviewBatch(payload: unknown, user: User) {
  const { documentIds } = batchApproveSchema.parse(payload);
  const client = createServiceClient();
  const now = new Date();
  const cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const { data: candidates, error: candidateError } = await client
    .from("documents")
    .select("id,created_at,published_at,content_tag,institution,document_sources(sources(content_type))")
    .in("id", documentIds)
    .in("workflow_status", ["NEW", "NEEDS_REVIEW"])
    .gte("created_at", cutoff);
  if (candidateError) throw new Error("일괄 승인 대상을 확인하지 못했습니다.");
  const eligibleIds = (candidates as BatchReviewRow[]).filter((row) => {
    const contentType = resolveSourceContentType(row.document_sources, row.content_tag, row.institution);
    return isBulkApprovalEligible(contentType, row.created_at, row.published_at, now);
  }).map((row) => row.id);
  if (eligibleIds.length === 0) throw new Error("승인 가능한 최신 검수 문서가 없습니다.");
  const { data, error } = await client
    .from("documents")
    .update({ workflow_status: "APPROVED" })
    .in("id", eligibleIds)
    .in("workflow_status", ["NEW", "NEEDS_REVIEW"])
    .select("id");
  if (error) throw new Error("일괄 승인에 실패했습니다.");
  const approvedIds = (data ?? []).map((document) => document.id);
  if (approvedIds.length === 0) throw new Error("승인 가능한 최신 검수 문서가 없습니다.");
  const { error: auditError } = await client.from("review_actions").insert(
    approvedIds.map((documentId) => ({
      document_id: documentId,
      actor_id: user.id,
      action: "APPROVE",
      after_data: { workflowStatus: "APPROVED", mode: "LATEST_BATCH" },
    })),
  );
  if (auditError) throw new Error("일괄 승인 감사 기록 저장에 실패했습니다.");
  return approvedIds.length;
}

export async function rejectReview(documentId: string, payload: unknown, user: User) {
  const value = rejectSchema.parse(payload);
  const client = createServiceClient();
  const { error } = await client.from("documents").update({ workflow_status: "REJECTED" }).eq("id", documentId);
  if (error) throw new Error("제외에 실패했습니다.");
  await recordAction(documentId, user, "REJECT", { workflowStatus: "REJECTED" }, value.reason);
}

export async function mergeReview(documentId: string, payload: unknown, user: User) {
  const value = mergeSchema.parse(payload);
  const client = createServiceClient();
  const { error } = await client.rpc("merge_documents", {
    source_document: documentId,
    target_document: value.targetDocumentId,
    actor: user.id,
    merge_reason: value.reason,
  });
  if (error) throw new Error("중복 문서 병합에 실패했습니다.");
}
