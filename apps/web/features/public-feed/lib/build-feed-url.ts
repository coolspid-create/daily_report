import type { TopicId } from "../constants/topics";

export function buildFeedUrl(
  topic: TopicId,
  archiveDate: string | null,
  currentDate: string | null,
  pressArchiveDate: string | null,
  currentPressDate: string | null,
): string {
  const params = new URLSearchParams();
  if (topic !== "all") params.set("topic", topic);
  if (archiveDate && archiveDate !== currentDate) params.set("date", archiveDate);
  if (pressArchiveDate && pressArchiveDate !== currentPressDate) params.set("pressDate", pressArchiveDate);
  const query = params.toString();
  return query ? `/?${query}` : "/";
}
