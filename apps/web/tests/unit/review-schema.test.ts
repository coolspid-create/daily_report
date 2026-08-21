import { describe, expect, it } from "vitest";
import { reviewFormSchema } from "@/features/admin-review/schemas/review-form.schema";

const valid = {
  canonicalTitle: "공공 AI 전략",
  institution: "국회입법조사처",
  publishedAt: "2026-08-21",
  primaryTopicId: "ai-tech",
  contentTag: "정책 변화",
  whyItMatters: "정책 방향을 빠르게 파악할 수 있습니다.",
  keyTags: ["핵심 1", "핵심 2", "핵심 3"],
  deliveryMode: "OFFICIAL_PAGE_ONLY",
};

describe("review schema", () => {
  it("accepts a complete review", () => expect(reviewFormSchema.parse(valid)).toEqual(valid));
  it("rejects more than three key tags", () => expect(() => reviewFormSchema.parse({ ...valid, keyTags: ["1", "2", "3", "4"] })).toThrow());
});
