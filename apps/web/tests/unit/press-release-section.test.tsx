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
    const { container } = render(<PressReleaseSection reports={[report]} archiveDate="2026-08-24" viewMode="list" />);

    expect(screen.getByText("01")).toHaveClass("press-list-num");
    expect(container.querySelector(".press-inst-badge")).toHaveTextContent("중앙부처 보도자료");

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

  it("renders PDF and source as separate report-style actions", () => {
    const reportWithPdf: PublicReport = {
      ...report,
      file: {
        ...report.file,
        deliveryMode: "DIRECT_OFFICIAL_FILE",
        downloadUrl: "https://example.com/press/1.pdf",
      },
    };

    render(<PressReleaseSection reports={[reportWithPdf]} archiveDate="2026-08-24" viewMode="list" />);

    const source = screen.getByRole("link", { name: /공식 원문 열기/ });
    const pdf = screen.getByRole("link", { name: /PDF ↓ 파일 다운로드/ });
    expect(source).toHaveClass("btn-action");
    expect(pdf).toHaveClass("btn-action", "btn-action-primary");
    expect(source).not.toHaveAttribute("href", pdf.getAttribute("href"));
  });

  it("reserves list action columns when a PDF is unavailable", () => {
    const { container } = render(<PressReleaseSection reports={[report]} archiveDate="2026-08-24" viewMode="list" />);

    expect(container.querySelectorAll(".press-list-actions .btn-action, .press-list-actions .btn-action-placeholder")).toHaveLength(3);
  });

  it("keeps the 보도자료 suffix as a separate source-name word", () => {
    const { container } = render(<PressReleaseSection reports={[{ ...report, institution: "산업통상자원부보도자료" }]} archiveDate="2026-08-24" viewMode="list" />);

    const badge = container.querySelector(".press-inst-badge") as HTMLElement;
    expect(badge).toHaveTextContent("산업통상자원부 보도자료");
    expect(badge.querySelector("span")).toHaveTextContent("보도자료");
  });
});
