import { describe, expect, it } from "vitest";
import { sortStoredDocuments } from "@/features/admin-review/server/get-review-history";
import type { StoredDocument } from "@/features/admin-review/types/admin-review";

describe("sortStoredDocuments", () => {
  const sampleDocs: StoredDocument[] = [
    {
      id: "doc-older-date",
      canonicalTitle: "어제 보도자료",
      institution: "기획재정부",
      publishedAt: "2026-08-23",
      primarySourceUrl: "https://example.com/1",
      workflowStatus: "APPROVED",
      createdAt: "2026-08-24T01:00:00Z",
      updatedAt: "2026-08-24T01:00:00Z",
      sourceContentType: "PRESS_RELEASE",
    },
    {
      id: "doc-today-first",
      canonicalTitle: "오늘 새벽 보도자료",
      institution: "산업통상자원부",
      publishedAt: "2026-08-24",
      primarySourceUrl: "https://example.com/2",
      workflowStatus: "APPROVED",
      createdAt: "2026-08-24T00:10:00Z",
      updatedAt: "2026-08-24T02:00:00Z",
      sourceContentType: "PRESS_RELEASE",
    },
    {
      id: "doc-today-latest-created",
      canonicalTitle: "오늘 최신 생성 보도자료",
      institution: "국토교통부",
      publishedAt: "2026-08-24",
      primarySourceUrl: "https://example.com/3",
      workflowStatus: "APPROVED",
      createdAt: "2026-08-24T05:30:00Z",
      updatedAt: "2026-08-24T01:00:00Z",
      sourceContentType: "PRESS_RELEASE",
    },
    {
      id: "doc-unknown-date",
      canonicalTitle: "날짜 미상 보도자료",
      institution: "공정거래위원회",
      publishedAt: "발행일 미상",
      primarySourceUrl: "https://example.com/4",
      workflowStatus: "APPROVED",
      createdAt: "2026-08-24T09:00:00Z",
      updatedAt: "2026-08-24T09:00:00Z",
      sourceContentType: "PRESS_RELEASE",
    },
  ];

  it("sorts press releases primarily by published_at DESC, then created_at DESC", () => {
    const sorted = sortStoredDocuments(sampleDocs, "PRESS_RELEASE");
    const ids = sorted.map((d) => d.id);

    expect(ids).toEqual([
      "doc-today-latest-created", // 2026-08-24, created 05:30
      "doc-today-first",          // 2026-08-24, created 00:10
      "doc-older-date",           // 2026-08-23
      "doc-unknown-date",         // 발행일 미상 -> last
    ]);
  });
});
