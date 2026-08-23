import { describe, expect, it } from "vitest";
import { reportsOnlySnapshot } from "@/features/public-feed/lib/content-type";
import type { PublicFeedSnapshot } from "@/features/public-feed/types/public-feed";

const snapshot = {
  version: 1,
  generatedAt: "2026-08-23T00:00:00.000Z",
  range: "7d",
  digests: {},
  topics: [
    { id: "all", label: "전체", count: 2 },
    { id: "economy", label: "경제·금융", count: 1 },
    { id: "industry", label: "산업·통상", count: 1 },
  ],
  reportsByTopic: {
    all: [
      { id: "report", title: "정책 보고서", institution: "연구원", publishedAt: "2026-08-23", contentTag: "보고서", isNew: true, analysisAvailable: true, shortSummary: "요약", keyTags: [], sourceContentType: "REPORT", file: { format: "PDF", sizeBytes: null, pageCount: null, deliveryMode: "OFFICIAL_PAGE_ONLY", downloadUrl: null, sourceUrl: "https://example.com/report" } },
      { id: "press", title: "보도자료", institution: "부처", publishedAt: "2026-08-23", contentTag: "보도자료", isNew: true, analysisAvailable: false, shortSummary: null, keyTags: [], sourceContentType: "PRESS_RELEASE", file: { format: null, sizeBytes: null, pageCount: null, deliveryMode: "OFFICIAL_PAGE_ONLY", downloadUrl: null, sourceUrl: "https://example.com/press" } },
    ],
    economy: [
      { id: "report", title: "정책 보고서", institution: "연구원", publishedAt: "2026-08-23", contentTag: "보고서", isNew: true, analysisAvailable: true, shortSummary: "요약", keyTags: [], sourceContentType: "REPORT", file: { format: "PDF", sizeBytes: null, pageCount: null, deliveryMode: "OFFICIAL_PAGE_ONLY", downloadUrl: null, sourceUrl: "https://example.com/report" } },
    ],
    industry: [
      { id: "press", title: "보도자료", institution: "부처", publishedAt: "2026-08-23", contentTag: "보도자료", isNew: true, analysisAvailable: false, shortSummary: null, keyTags: [], sourceContentType: "PRESS_RELEASE", file: { format: null, sizeBytes: null, pageCount: null, deliveryMode: "OFFICIAL_PAGE_ONLY", downloadUrl: null, sourceUrl: "https://example.com/press" } },
    ],
  },
} satisfies PublicFeedSnapshot;

describe("reportsOnlySnapshot", () => {
  it("excludes press releases and recalculates every topic count", () => {
    const result = reportsOnlySnapshot(snapshot);

    expect(result.reportsByTopic.all).toHaveLength(1);
    expect(result.reportsByTopic.industry).toEqual([]);
    expect(result.topics.map(({ id, count }) => [id, count])).toEqual([
      ["all", 1],
      ["economy", 1],
      ["industry", 0],
    ]);
  });
});
