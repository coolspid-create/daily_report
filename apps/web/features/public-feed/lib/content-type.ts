import type { PublicFeedSnapshot } from "../types/public-feed";
import type { PublicReport, SourceContentType } from "../types/public-report";

const LEGACY_PRESS_INSTITUTIONS = ["보도자료"];

export function sourceContentType(report: PublicReport): SourceContentType {
  if (report.sourceContentType) return report.sourceContentType;
  if (report.contentTag === "보도자료") return "PRESS_RELEASE";
  return LEGACY_PRESS_INSTITUTIONS.some((term) => report.institution.includes(term))
    ? "PRESS_RELEASE"
    : "REPORT";
}

export function isPressRelease(report: PublicReport): boolean {
  return sourceContentType(report) === "PRESS_RELEASE";
}

export function reportsOnlySnapshot(snapshot: PublicFeedSnapshot): PublicFeedSnapshot {
  const reportsByTopic = Object.fromEntries(
    Object.entries(snapshot.reportsByTopic).map(([topic, reports]) => [
      topic,
      reports.filter((report) => !isPressRelease(report)),
    ]),
  );
  return {
    ...snapshot,
    reportsByTopic,
    topics: snapshot.topics.map((topic) => ({
      ...topic,
      count: reportsByTopic[topic.id]?.length ?? 0,
    })),
  };
}
