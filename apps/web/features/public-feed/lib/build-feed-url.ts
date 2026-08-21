import type { TopicId } from "../constants/topics";
export function buildFeedUrl(topic: TopicId, archiveDate: string | null, currentDate: string | null): string {
  const params = new URLSearchParams();
  if (topic !== "all") params.set("topic", topic);
  if (archiveDate && archiveDate !== currentDate) params.set("date", archiveDate);
  const query = params.toString();
  return query ? `/?${query}` : "/";
}
