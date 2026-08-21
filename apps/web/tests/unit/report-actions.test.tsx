import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportActions } from "@/features/public-feed/components/report-actions";
import type { ReportFile } from "@/features/public-feed/types/public-report";

const base: ReportFile = { format: "PDF", sourceUrl: "https://official.example/report", deliveryMode: "OFFICIAL_PAGE_ONLY" };

describe("report actions", () => {
  it.each([
    ["DIRECT_OFFICIAL_FILE", "PDF ↓"],
    ["MIRRORED_ALLOWED", "PDF ↓"],
    ["OFFICIAL_PAGE_ONLY", "원문 ↗"],
  ] as const)("renders %s correctly", (deliveryMode, label) => {
    const downloadUrl = deliveryMode === "OFFICIAL_PAGE_ONLY" ? null : "https://official.example/report.pdf";
    render(<ReportActions file={{ ...base, deliveryMode, downloadUrl }} />);
    expect(screen.getByRole("link", { name: new RegExp(label) })).toHaveAttribute("rel", "noopener noreferrer");
  });

  it.each(["SUMMARY_ONLY", "BLOCKED"] as const)("does not render a download for %s", (deliveryMode) => {
    render(<ReportActions file={{ ...base, deliveryMode }} />);
    expect(screen.queryByText("PDF ↓")).not.toBeInTheDocument();
    expect(screen.getByText("원문 ↗")).toBeVisible();
  });
});
