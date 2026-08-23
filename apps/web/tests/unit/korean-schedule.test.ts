import { describe, expect, it } from "vitest";
import { isKoreanCollectionWeekday } from "@/features/automation/server/korean-schedule";

describe("Korean collection schedule", () => {
  it("accepts Monday through Friday in Asia/Seoul", () => {
    expect(isKoreanCollectionWeekday(new Date("2026-08-23T23:35:00Z"))).toBe(true);
    expect(isKoreanCollectionWeekday(new Date("2026-08-27T23:35:00Z"))).toBe(true);
  });

  it("rejects Saturday and Sunday in Asia/Seoul", () => {
    expect(isKoreanCollectionWeekday(new Date("2026-08-21T23:35:00Z"))).toBe(false);
    expect(isKoreanCollectionWeekday(new Date("2026-08-22T23:35:00Z"))).toBe(false);
  });
});
