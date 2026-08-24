import { describe, expect, it } from "vitest";
import {
  isBulkApprovalEligible,
  isWithinPublicationWindow,
  isWithinReviewWindow,
} from "@/features/admin-review/lib/review-eligibility";

const now = new Date("2026-08-24T01:00:00.000Z");

describe("review eligibility", () => {
  it("keeps recently ingested exceptions in the review queue", () => {
    expect(isWithinReviewWindow("REPORT", "2026-08-24T00:00:00.000Z", now)).toBe(true);
  });

  it("rejects old or missing publication dates from bulk approval", () => {
    expect(isBulkApprovalEligible("REPORT", "2026-08-24T00:00:00.000Z", "2024-12-31", now)).toBe(false);
    expect(isBulkApprovalEligible("REPORT", "2026-08-24T00:00:00.000Z", null, now)).toBe(false);
  });

  it("accepts a recent report only when both windows match", () => {
    expect(isBulkApprovalEligible("REPORT", "2026-08-24T00:00:00.000Z", "2026-08-23", now)).toBe(true);
  });

  it("uses the shorter publication window for press releases", () => {
    expect(isWithinPublicationWindow("PRESS_RELEASE", "2026-08-23", now)).toBe(true);
    expect(isWithinPublicationWindow("PRESS_RELEASE", "2026-08-22", now)).toBe(false);
  });
});
