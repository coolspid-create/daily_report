import { describe, expect, it } from "vitest";
import { resolveSourceContentType } from "@/features/admin-review/server/source-content-type";
import { toPublicReport } from "@/features/public-feed/server/get-press-releases";

describe("resolveSourceContentType", () => {
  it("resolves PRESS_RELEASE from content tag", () => {
    expect(resolveSourceContentType([], "보도자료", "기관")).toBe("PRESS_RELEASE");
  });

  it("resolves PRESS_RELEASE from institution", () => {
    expect(resolveSourceContentType([], "정책", "기획재정부 보도자료")).toBe("PRESS_RELEASE");
  });

  it("resolves PRESS_RELEASE from source array", () => {
    const sources = [
      {
        sources: [{ content_type: "PRESS_RELEASE" as const }],
      },
    ];
    expect(resolveSourceContentType(sources)).toBe("PRESS_RELEASE");
  });

  it("resolves REPORT by default for research sources", () => {
    const sources = [
      {
        sources: [{ content_type: "REPORT" as const }],
      },
    ];
    expect(resolveSourceContentType(sources)).toBe("REPORT");
  });

  it("keeps an explicit report source even when legacy text resembles press data", () => {
    const sources = [
      {
        sources: [{ content_type: "REPORT" as const }],
      },
    ];
    expect(resolveSourceContentType(sources, "보도자료", "연구원 보도자료")).toBe("REPORT");
  });
});

describe("toPublicReport", () => {
  it("supports auto-approved documents without analysis or file relations", () => {
    const report = toPublicReport({
      id: "press-without-analysis",
      canonical_title: "분석 대기 보도자료",
      institution: "정부기관",
      published_at: "2026-08-26",
      content_tag: "보도자료",
      why_it_matters: null,
      primary_source_url: "https://example.go.kr/press/1",
      delivery_mode: "OFFICIAL_PAGE_ONLY",
      created_at: "2026-08-26T00:00:00Z",
      updated_at: "2026-08-26T00:00:00Z",
      document_analysis: null,
      document_files: null,
      document_sources: [],
    });

    expect(report.analysisAvailable).toBe(false);
    expect(report.shortSummary).toBeNull();
    expect(report.file.downloadUrl).toBeNull();
    expect(report.file.sourceUrl).toBe("https://example.go.kr/press/1");
  });
});
