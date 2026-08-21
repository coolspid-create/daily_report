import { describe, expect, it } from "vitest";
import rawSnapshots from "@/data/public-snapshots.json";
import { validatePublicSnapshot } from "@/features/public-feed/server/validate-public-snapshot";

describe("public snapshot contract", () => {
  it("accepts a seven-day public snapshot", () => {
    expect(validatePublicSnapshot({ ...rawSnapshots["1d"], range: "7d" }).range).toBe("7d");
  });

  it("rejects unapproved internal fields", () => {
    expect(() => validatePublicSnapshot({ ...rawSnapshots.today, providerKey: "secret" })).toThrow("Invalid public feed snapshot");
  });

  it("ships only direct file or report-detail destinations", () => {
    const reports = rawSnapshots["1d"].reportsByTopic.all;
    for (const report of reports) {
      const source = new URL(report.file.sourceUrl);
      expect(source.pathname).not.toBe("/");
      if (report.file.deliveryMode === "DIRECT_OFFICIAL_FILE") {
        expect(report.file.downloadUrl).toContain("fileDownload");
      }
    }
  });
});
