import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportFeedItem } from "@/features/public-feed/components/report-feed-item";
import type { PublicReport } from "@/features/public-feed/types/public-report";

const report: PublicReport = {
  id: "summary-report",
  title: "본문 요약이 있는 보고서",
  institution: "공공연구원",
  publishedAt: "2026-08-21",
  contentTag: "본문 요약",
  isNew: true,
  analysisAvailable: true,
  shortSummary: "첫 번째 본문 문장입니다. 두 번째 본문 문장입니다. 세 번째 본문 문장입니다.",
  keyTags: ["본문", "정책", "검토"],
  file: { format: "PDF", deliveryMode: "OFFICIAL_PAGE_ONLY", sourceUrl: "https://example.com/report" },
};

describe("ReportFeedItem", () => {
  it("expands and collapses a source-derived summary in place", () => {
    render(<ReportFeedItem report={report} />);
    const toggle = screen.getByRole("button", { name: "더보기" });
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("button", { name: "요약 접기" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "요약 접기" }));
    expect(screen.getByRole("button", { name: "더보기" })).toHaveAttribute("aria-expanded", "false");
  });
});
