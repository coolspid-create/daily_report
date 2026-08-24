import type { SourceContentType } from "../types/admin-review";

const REVIEW_WINDOW_HOURS: Record<SourceContentType, number> = {
  REPORT: 168,
  PRESS_RELEASE: 24,
};

const SEOUL_DATE_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Seoul",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function toSeoulDateKey(date: Date): string {
  const parts = Object.fromEntries(
    SEOUL_DATE_FORMATTER.formatToParts(date).map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function publishedDateKey(value: string | null): string | null {
  return value?.match(/^\d{4}-\d{2}-\d{2}/)?.[0] ?? null;
}

export function isWithinReviewWindow(
  contentType: SourceContentType,
  createdAt: string | null,
  now = new Date(),
): boolean {
  if (!createdAt) return false;
  const created = new Date(createdAt);
  if (Number.isNaN(created.getTime())) return false;

  const ageMs = now.getTime() - created.getTime();
  const maxAgeMs = REVIEW_WINDOW_HOURS[contentType] * 60 * 60 * 1000;
  return ageMs >= 0 && ageMs <= maxAgeMs;
}

export function isWithinPublicationWindow(
  contentType: SourceContentType,
  publishedAt: string | null,
  now = new Date(),
): boolean {
  const published = publishedDateKey(publishedAt);
  if (!published) return false;

  const start = new Date(now.getTime() - REVIEW_WINDOW_HOURS[contentType] * 60 * 60 * 1000);
  return published >= toSeoulDateKey(start) && published <= toSeoulDateKey(now);
}

export function isBulkApprovalEligible(
  contentType: SourceContentType,
  createdAt: string | null,
  publishedAt: string | null,
  now = new Date(),
): boolean {
  return (
    isWithinReviewWindow(contentType, createdAt, now) &&
    isWithinPublicationWindow(contentType, publishedAt, now)
  );
}
