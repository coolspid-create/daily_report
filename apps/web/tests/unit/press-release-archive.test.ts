import { describe, expect, it } from "vitest";
import { resolveSourceContentType } from "@/features/admin-review/server/source-content-type";

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
