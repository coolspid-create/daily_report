import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PressReleaseSection } from "@/features/public-feed/components/press-release-section";
import type { PublicReport } from "@/features/public-feed/types/public-report";

const report: PublicReport = {
  id: "press-1",
  title: "보도자료 제목",
  institution: "중앙부처 보도자료",
  publishedAt: "2026-08-24",
  contentTag: "보도자료",
  isNew: true,
  analysisAvailable: true,
  shortSummary: "보도자료의 전체 요약 내용입니다.",
  keyTags: ["정책", "현장"],
  file: {
    format: "PDF",
    deliveryMode: "OFFICIAL_PAGE_ONLY",
    sourceUrl: "https://example.com/press/1",
  },
};

describe("PressReleaseSection", () => {
  it("expands a press summary in list view", () => {
    render(<PressReleaseSection reports={[report]} archiveDate="2026-08-24" viewMode="list" />);

    const title = screen.getByRole("button", { name: "보도자료 제목" });
    fireEvent.click(title);

    expect(title).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("보도자료의 전체 요약 내용입니다.")).toBeVisible();
    expect(screen.getByRole("button", { name: "요약 접기" })).toBeVisible();
  });

  it("shows the full press summary without a toggle in grid view", () => {
    render(<PressReleaseSection reports={[report]} archiveDate="2026-08-24" viewMode="grid" />);

    expect(screen.getByRole("heading", { name: "보도자료 제목" })).toBeVisible();
    expect(screen.getByText("보도자료의 전체 요약 내용입니다.")).toBeVisible();
    expect(screen.queryByRole("button", { name: "더보기" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "요약 접기" })).not.toBeInTheDocument();
  });
});
